import json

from pypdf import PdfReader

from ..db.queries import (
    insert_bullet,
    insert_education,
    insert_profile,
    insert_skill,
    insert_volunteer,
    upsert_job,
)


def extract_enhancv_data(pdf_path):
    reader = PdfReader(pdf_path)
    metadata = reader.metadata
    
    if '/ecv-data' not in metadata:
        raise ValueError("No EnhancCV data found in PDF metadata.")
    
    raw_data = metadata['/ecv-data']

    # Known edge case, not yet hit against a real export: pypdf decodes a PDF
    # string containing only ASCII characters to plain text directly, so the
    # latin1->utf16 re-decode below has nothing to fail on -- it "succeeds"
    # and produces garbage instead of raising. That garbage then fails
    # json.loads(), which the outer except still converts to a clear
    # ValueError, so this doesn't corrupt data -- but it would misreport an
    # all-ASCII export as a decode failure instead of importing it. Fixture:
    # scripts/make_sample_ecv_fixture.py deliberately includes a non-ASCII
    # character (an em dash) to take the branch real EnhancCV exports use.
    try:
        if isinstance(raw_data, str):
            try:
                data_str = raw_data.encode('latin1').decode('utf-16')
            except (UnicodeEncodeError, UnicodeDecodeError):
                data_str = raw_data
        else:
            data_str = raw_data.decode('utf-16')

        return json.loads(data_str)
    except Exception as e:  # noqa: BLE001 - several failure modes (UnicodeDecodeError, JSONDecodeError) all convert to the same domain error
        raise ValueError(f"Failed to decode EnhancCV data: {e}")

def import_enhancv(pdf_path, db_conn):
    data = extract_enhancv_data(pdf_path)
    
    # Map header to profile
    header = data.get('header', {})
    name = header.get('name')
    if name:
        links = header.get('links', [])
        linkedin = next((link['url'] for link in links if link['title'].lower() == 'linkedin'), None)
        github = next((link['url'] for link in links if link['title'].lower() == 'github'), None)
        website = next((link['url'] for link in links if link['title'].lower() == 'website'), None)
        
        insert_profile(
            db_conn,
            name=name,
            email=header.get('email'),
            phone=header.get('phone'),
            location=header.get('location'),
            linkedin=linkedin,
            github=github,
            website=website,
            summary=header.get('summary')
        )
    
    # Map sections
    for section in data.get('sections', []):
        section_type = section.get('type')
        items = section.get('items', [])
        
        if section_type == 'ExperienceSection':
            for item in items:
                company = item.get('company', {}).get('text')
                role = item.get('role', {}).get('text')
                start_date = item.get('startDate')
                
                if company and role and start_date:
                    job_id = upsert_job(
                        db_conn,
                        company=company,
                        role=role,
                        start_date=start_date,
                        end_date=item.get('endDate'),
                        location=item.get('location')
                    )
                    
                    for bullet in item.get('description', []):
                        content = bullet.get('text')
                        if content:
                            insert_bullet(db_conn, job_id, content)
                            
        elif section_type == 'TalentSection':
            for item in items:
                skill_name = item.get('text')
                if skill_name:
                    insert_skill(db_conn, name=skill_name, category='technical')
                    
        elif section_type == 'EducationSection':
            for item in items:
                institution = item.get('institution')
                if institution:
                    insert_education(
                        db_conn,
                        institution=institution,
                        degree=item.get('degree'),
                        field=item.get('field'),
                        year=item.get('year')
                    )
                    
        elif section_type == 'VolunteerSection':
            for item in items:
                organization = item.get('organization')
                vol_role = item.get('role')
                if organization and vol_role:
                    insert_volunteer(
                        db_conn,
                        organization=organization,
                        role=vol_role,
                        description=item.get('description'),
                        start_date=item.get('startDate'),
                        end_date=item.get('endDate')
                    )
    
    return data
