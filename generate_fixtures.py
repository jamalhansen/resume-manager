import json
import zipfile
import io
import csv
from pypdf import PdfWriter

def create_synthetic_ecv(output_path):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    
    # Mock EnhancCV data
    data = {
        "header": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "location": "New York, NY",
            "links": [{"title": "linkedin", "url": "https://linkedin.com/in/janedoe"}]
        },
        "sections": [
            {
                "type": "ExperienceSection",
                "items": [
                    {
                        "company": {"text": "Tech Corp"},
                        "role": {"text": "Senior Engineer"},
                        "startDate": "2020-01",
                        "endDate": "Present",
                        "location": "Remote",
                        "description": [
                            {"text": "Led a team of 5 to deliver X."},
                            {"text": "Improved performance by 30%."}
                        ]
                    }
                ]
            },
            {
                "type": "TalentSection",
                "items": [
                    {"text": "Python", "level": 5},
                    {"text": "SQL", "level": 4}
                ]
            },
            {
                "type": "EducationSection",
                "items": [
                    {
                        "institution": "State University",
                        "degree": "BS in CS",
                        "year": "2018"
                    }
                ]
            }
        ]
    }
    
    # Encode as UTF-16
    data_str = json.dumps(data)
    encoded_data = data_str.encode('utf-16')
    
    writer.add_metadata({
        '/ecv-data': encoded_data.decode('latin1')
    })
    
    with open(output_path, "wb") as f:
        writer.write(f)

def create_synthetic_linkedin(output_path):
    with zipfile.ZipFile(output_path, 'w') as z:
        # Profile.csv
        profile_io = io.StringIO()
        writer = csv.DictWriter(profile_io, fieldnames=["First Name", "Last Name", "Email Address", "Address", "Websites"])
        writer.writeheader()
        writer.writerow({
            "First Name": "Jane",
            "Last Name": "Doe",
            "Email Address": "jane@example.com",
            "Address": "New York, NY",
            "Websites": "[COMPANY_WEBSITE:https://jane.com,LINKEDIN:https://linkedin.com/in/janedoe]"
        })
        z.writestr("Profile.csv", profile_io.getvalue())
        
        # Positions.csv
        positions_io = io.StringIO()
        writer = csv.DictWriter(positions_io, fieldnames=["Company Name", "Title", "Description", "Location", "Started On", "Finished On"])
        writer.writeheader()
        writer.writerow({
            "Company Name": "Tech Corp",
            "Title": "Senior Engineer",
            "Description": "Led a team of 5 to deliver X.\nImproved performance by 30%.",
            "Location": "Remote",
            "Started On": "Jan 2020",
            "Finished On": ""
        })
        z.writestr("Positions.csv", positions_io.getvalue())
        
        # Education.csv
        education_io = io.StringIO()
        writer = csv.DictWriter(education_io, fieldnames=["School Name", "Degree Name", "Notes", "Started On", "Finished On"])
        writer.writeheader()
        writer.writerow({
            "School Name": "State University",
            "Degree Name": "BS in CS",
            "Notes": "",
            "Started On": "2014",
            "Finished On": "2018"
        })
        z.writestr("Education.csv", education_io.getvalue())

if __name__ == "__main__":
    create_synthetic_ecv("tests/fixtures/sample_ecv.pdf")
    create_synthetic_linkedin("tests/fixtures/sample_linkedin.zip")
