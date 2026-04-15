import zipfile
import csv
import io

from ..db.queries import insert_profile, upsert_job, insert_bullet, insert_education

def import_linkedin(zip_path, db_conn):
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Profile.csv
        if 'Profile.csv' in z.namelist():
            with z.open('Profile.csv') as f:
                reader = csv.DictReader(io.TextIOWrapper(f))
                for row in reader:
                    name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()
                    if name:
                        websites = row.get('Websites', '')
                        linkedin = None
                        website = None
                        if '[' in websites:
                            # Simple extraction for [LINKEDIN:https://...]
                            import re
                            li_match = re.search(r'LINKEDIN:(https?://[^,\]]+)', websites)
                            if li_match:
                                linkedin = li_match.group(1)
                            ws_match = re.search(r'COMPANY_WEBSITE:(https?://[^,\]]+)', websites)
                            if ws_match:
                                website = ws_match.group(1)
                        
                        insert_profile(
                            db_conn,
                            name=name,
                            email=row.get('Email Address'),
                            phone=row.get('Phone Numbers'),
                            location=row.get('Address'),
                            linkedin=linkedin,
                            website=website
                        )
        
        # Positions.csv
        if 'Positions.csv' in z.namelist():
            with z.open('Positions.csv') as f:
                reader = csv.DictReader(io.TextIOWrapper(f))
                for row in reader:
                    company = row.get('Company Name')
                    role = row.get('Title')
                    start_date = row.get('Started On')
                    if company and role and start_date:
                        job_id = upsert_job(
                            db_conn,
                            company=company,
                            role=role,
                            start_date=start_date,
                            end_date=row.get('Finished On'),
                            location=row.get('Location')
                        )
                        
                        description = row.get('Description')
                        if description:
                            # Split by newline or bullet characters
                            bullets = [b.strip() for b in description.split('\n') if b.strip()]
                            for bullet in bullets:
                                insert_bullet(db_conn, job_id, bullet)
        
        # Education.csv
        if 'Education.csv' in z.namelist():
            with z.open('Education.csv') as f:
                reader = csv.DictReader(io.TextIOWrapper(f))
                for row in reader:
                    institution = row.get('School Name')
                    if institution:
                        insert_education(
                            db_conn,
                            institution=institution,
                            degree=row.get('Degree Name'),
                            year=row.get('Finished On')
                        )
        
        # Certifications.csv
        if 'Certifications.csv' in z.namelist():
            with z.open('Certifications.csv') as f:
                reader = csv.DictReader(io.TextIOWrapper(f))
                for row in reader:
                    institution = row.get('Authority')
                    if institution:
                        insert_education(
                            db_conn,
                            institution=institution,
                            degree=row.get('Name'),
                            year=row.get('Finished On'),
                            is_certification=1
                        )
