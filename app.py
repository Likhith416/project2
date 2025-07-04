import httpx
import motor.motor_asyncio
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from werkzeug.utils import secure_filename
from bson import ObjectId
import tornado.ioloop
import tornado.web
# import bcrypt
import email
import io
import json
from email.message import EmailMessage
import os

# MongoDB Connection
MONGO_URI = "mongodb+srv://likhth1234:nani0416@cluster04.uyhboig.mongodb.net/"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["testdb"]
users_collection = db["users"]

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
fs = AsyncIOMotorGridFSBucket(db)

# Base Handler (Handles CORS & Authentication Check)
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_email = self.get_secure_cookie("user_email")
        if user_email:
            print(f"🔍 Cookie Retrieved: {user_email.decode()}")  # Debugging
            return user_email.decode()
        else:
            print("⚠️ No user_email cookie found.")  # Debugging
            return None
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def check_authentication(self):
        user_email = self.get_secure_cookie("user_email")
        admin_email = self.get_secure_cookie("admin")

        if admin_email:
            print(f"🔒 Admin authenticated: {admin_email.decode()}")  # Debugging
            return True  # Admin is authenticated

        if user_email:
            print(f"🔒 User authenticated: {user_email.decode()}")  # Debugging
            return True  # User is authenticated

        print("⚠️ User not authenticated. Redirecting to login.")  # Debugging
        self.redirect("/")  # Redirect to login for both admin and user
        return False


    def options(self):
        self.set_status(204)
        self.finish()

class AuthAdminHandler(tornado.web.RequestHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body.decode("utf-8"))
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                self.write({"success": False, "error": "Missing email or password"})
                return

            # Find admin user in the database
            admin = await users_collection.find_one({"email": email, "password": password, "role": "admin"})

            if admin:
                admin_data = {
                    "id": str(admin["_id"]),
                    "username": admin["name"],
                    "email": admin.get("email", ""),
                    "mobile": admin.get("mobile", ""),
                    "role": "admin"
                }
                
                # Set a secure cookie for session management
                self.set_secure_cookie("admin", email, httponly=True, secure=False)  # Set secure=True in production

                self.write({"success": True, "admin": admin_data})
            else:
                self.write({"success": False, "error": "Invalid credentials"})

        except Exception as e:
            self.write({"success": False, "error": str(e)})
# class AuthAdminHandler(tornado.web.RequestHandler):
#     async def post(self):
#         try:
#             data = json.loads(self.request.body.decode("utf-8"))
#             email = data.get("email")
#             password = data.get("password")

#             if not email or not password:
#                 self.write({"success": False, "error": "Missing email or password"})
#                 return

#             # Find admin user in the database
#             admin = await users_collection.find_one({"email": email, "password": password, "role": "admin"})

#             if admin:
#                 admin_data = {
#                     "id": str(admin["_id"]),
#                     "username": admin["name"],
#                     "email": admin.get("email", ""),
#                     "mobile": admin.get("mobile", ""),
#                     "role": "admin"
#                 }
                
#                 # Set a secure cookie for session management
#                 self.set_secure_cookie("admin", email, httponly=True)

#                 self.write({"success": True, "admin": admin_data})
#             else:
#                 self.write({"success": False, "error": "Invalid credentials"})

#         except Exception as e:
#             self.write({"success": False, "error": str(e)})


class AuthHandler(tornado.web.RequestHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body.decode("utf-8"))
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                self.write({"success": False, "error": "Missing email or password"})
                return

            # Find user in the database by email
            user = await users_collection.find_one({"email": email, "password": password, "role": "user"})

            if user:
                user_data = {
                    "id": str(user["_id"]),
                    "username": user["name"],
                    "email": user.get("email", ""),
                    "mobile": user.get("mobile", ""),
                    "role": "user",
                }
                
                # ✅ Store email securely in a cookie
                self.set_secure_cookie("user_email", email, expires_days=1, httponly=False, secure=False, samesite="Lax")


                print(f"✅ Cookie set for user: {email}")  # Debugging

                self.write({"success": True, "user": user_data})
            else:
                self.write({"success": False, "error": "Invalid credentials"})

        except Exception as e:
            print(f"🚨 Error in AuthHandler: {str(e)}")  # Log the error
            self.write({"success": False, "error": str(e)})


# Page Handlers
class LoginPageHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            self.render("login.html")
        except Exception as e:
            self.write({"success": False, "error": str(e)})

class UserHomePageHandler(BaseHandler):
    def get(self):
        if self.check_authentication():
            self.render("userhome.html")

class AdminHomePageHandler(BaseHandler):
    def get(self):
        if self.check_authentication():
            self.render("adminpg.html")

import re
class RegisterUserHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("registration.html")

    async def post(self):
        try:
            username = self.get_body_argument("username", "")
            email = self.get_body_argument("email", "")
            mobile = self.get_body_argument("mobile", "")
            password = self.get_body_argument("password", "")
            role = self.get_body_argument("role", "")

            # Email validation
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_regex, email):
                self.write({"success": False, "error": "Invalid email format."})
                return

            # Check if email already exists
            if await users_collection.count_documents({'email': email}) > 0:
                self.write({"success": False, "error": "Email already exists"})
                return

            # Store user details in MongoDB (without CV)
            user = {
                "name": username,
                "email": email,
                "mobile": mobile,
                "password": password,  # Storing in plain text for now
                "role": role
            }
            result = await users_collection.insert_one(user)

            if result.inserted_id:
                # Set the cookie for the newly registered user
                self.set_secure_cookie("user_email", email)
                self.write({"success": True})
                return

            self.write({"success": False, "error": "Registration failed."})

        except Exception as e:
            self.write({"success": False, "error": str(e)})




# ✅ Route to Serve `upload_preferred_cv.html`
class UploadPreferredCVPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("upload_preferred_cv.html")  # Make sure this file is inside 'templates/'
    async def post(self):
        self.write({"success": False, "error": "Use POST to upload a CV."})  # Prevents 405 errors
class ResultsPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("result.html")  # Ensure results.html is in your templates folder

 
# ✅ API Route to Handle CV Uploads
class UploadCVHandler(BaseHandler):
    async def post(self):
        try:
            if "file" not in self.request.files:
                self.write({"success": False, "error": "No CV file uploaded"})
                return

            cv_file = self.request.files["file"][0]
            filename = secure_filename(cv_file["filename"])

            if not filename or not filename.lower().endswith((".pdf", ".docx")):
                self.write({"success": False, "error": "Invalid file format. Only PDF/DOCX allowed."})
                return

            # ✅ Fix: Use correct encoding for HTTPX file upload
            files = {
                "file": (filename, cv_file["body"], "application/octet-stream")
            }

            data = {
                "model": self.get_body_argument("model",default= "logistic_regression")
            }

            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:5000/upload-preferred-cv", files=files, data=data)

            self.write(response.json())

        except Exception as e:
            self.write({"success": False, "error": str(e)})

class EditProfileHandler(BaseHandler):
    def get(self):
        if self.check_authentication():
            self.render("editprofile.html")

    async def post(self):
        try:
            data = json.loads(self.request.body)
            email = data.get("email")

            if not email:
                self.write({"success": False, "error": "Email is required"})
                return

            update_fields = {key: data[key] for key in ["name", "mobile", "password"] if key in data}

            result = await users_collection.update_one({"email": email}, {"$set": update_fields})

            self.write({"success": bool(result.modified_count)})
        except Exception as e:
            self.write({"success": False, "error": str(e)})

# Test Pages

class AptitudeTestHandler(BaseHandler):
    async def get(self):
        if self.check_authentication():
            questions = await db["users"].find({"test_type": "aptitude"}).to_list(length=100)
            self.render("aptitudetest.html", questions=questions)
class ProgrammingTestHandler(BaseHandler):
    async def get(self):
        email = self.get_secure_cookie("user_email")
        if email:
            email = email.decode()
        self.render("programmingtest.html", user_email=email)


class GetUserScoresHandler(BaseHandler):
    async def get(self):
        if self.check_authentication():
            user_email = self.get_cookie("email")
            user_scores = await users_collection.find_one({"email": user_email}, {"Aptitude Test Score": 1, "Programming Test Score": 1})
            if user_scores:
                print(user_scores)
                self.write({"success": True, "scores": {
                    "Aptitude": user_scores.get("Aptitude Test Score", 0),
                    "Programming": user_scores.get("Programming Test Score", 0)
                }})
            else:
                self.write({"success": False, "scores": {"Aptitude": 0, "Programming": 0}})

class ResultsHandler(BaseHandler):
    def get(self):
        if self.check_authentication():
            self.render("results.html")

# New endpoint to fetch user scores
class FetchUserScoresHandler(BaseHandler):
    async def get(self):
        try:
            users = await users_collection.find({"role": "user"}, {"email": 1, "Aptitude Test Score": 1, "Programming Test Score": 1, "Aptitude Test percentage": 1, "programming Test percentage": 1}).to_list(length=100)
            users = [{**user, "_id": str(user["_id"])} for user in users]  # Convert ObjectId to string
            print(users)
            self.write({"success": True, "data": users})
        except Exception as e:
            self.set_status(500)
            print(e)
            self.write({"success": False, "error": str(e)})
class FetchSortListedHandler(BaseHandler):
    async def get(self):
        try:
            print("Fetching shortlisted users...")  # Debug log
            shortlisted_users = await users_collection.find(
                {
                        "role": "user",
                },
                {
                    "email": 1, "Aptitude Test Score": 1, "programming Test Score": 1,
                    "Aptitude Test Percentage": 1, "programming Test Percentage": 1, "cv_id": 1
                }
            ).to_list(length=100)
            res = []
            print("Users fetched:", shortlisted_users)  # Debug output
            for user in shortlisted_users:
                #user["_id"] = str(user["_id"])  # Convert ObjectId to string
                if "_id" in user and isinstance(user["_id"], ObjectId):
                    user["_id"] = str(user["_id"])
                user["Aptitude Test Percentage"] = float(user["Aptitude Test Percentage"]) if "Aptitude Test Percentage" in user else 0
                user["programming Test Percentage"] = float(user["programming Test Percentage"]) if "programming Test Percentage" in user else 0
                if "cv_id" in user and isinstance(user["cv_id"], ObjectId):
                    user["cv_id"] = str(user.get("cv_id",''))
                if not ( user["Aptitude Test Percentage"]>=75 and user["programming Test Percentage"]>=75):
                    continue
                user["cv_download_url"] = f"/download_cv/{user['cv_id']}" if "cv_id" in user else ''
                res.append(user)

            self.write({"success": True, "data": json.dumps(res)})
        
        except Exception as e:
            print("Error in FetchSortListedHandler:", str(e))  # Debug error
            self.set_status(500)
            self.write({"success": False, "error": str(e)})
import json
from bson import ObjectId

class AddJobDetailsHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            job_id = data.get("job_id")
            designation = data.get("designation")
            salary = data.get("salary")
            place = data.get("place")

            if not job_id:
                self.write({"success": False, "error": "Job ID is required"})
                return

            # Check if job_id already exists in the database
            existing_job = await db["job_details"].find_one({"job_id": job_id})
            if existing_job:
                self.write({"success": False, "error": "Job ID already exists"})
                return

            # Store job details in MongoDB if job_id is not found
            job_details = {
                "job_id": job_id,
                "designation": designation,
                "salary": salary,
                "place": place
            }
            result = await db["job_details"].insert_one(job_details)

            self.write({"success": bool(result.inserted_id)})

        except Exception as e:
            self.write({"success": False, "error": str(e)})
class JobRequirementsHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            print(data)
            job_id = data.get("job_id")
            experience = data.get("experience")
            qualification = data.get("qualification")
            keyskills = data.get("keyskills")

            if keyskills:
                keyskills = keyskills.lower()

            if not job_id:
                self.write({"success": False, "error": "Job ID is required"})
                return

            # Check if job_id already exists in the database
            existing_job = await db["job_Requirement_details"].find_one({"job_id": job_id})
            if existing_job:
                self.write({"success": False, "error": "Job ID already exists"})
                return

            # Store job details in MongoDB if job_id is not found
            job_details = {
                "job_id": job_id,
                "experience": experience,
                "qualification": qualification,
                "keyskills": keyskills
            }
            result = await db["job_Requiremtent_details"].insert_one(job_details)

            self.write({"success": bool(result.inserted_id)})

        except Exception as e:
            self.write({"success": False, "error": str(e)})


# Add the new route to the application
class AddQuestionHandler(BaseHandler):
    def get(self):
        self.render("admintests.html")

    async def post(self):
        try:
            data = json.loads(self.request.body)
            category = data.get("category")
            question_type = data.get("type")
            question = data.get("question")
            options = data.get("options", [])

            doc = {
                "category": category,
                "type": question_type,
                "question": question
            }

            if question_type.lower() == "aptitude":
                doc["options"] = options
                doc["correctAnswer"] = data.get("correctAnswer")

            elif question_type.lower() == "coding" or question_type.lower() == "programming":
                doc["expectedOutput"] = data.get("expectedOutput")
                doc["codeSnippet"] = data.get("codeSnippet", "")
                

            result = await db["questions"].insert_one(doc)

            self.write({
                "success": bool(result.inserted_id),
                "questionId": str(result.inserted_id)
            })

        except Exception as e:
            self.write({
                "success": False,
                "error": str(e)
            })




# Static File Handler (for serving HTML files)
class StaticFileHandler(tornado.web.StaticFileHandler):
    def get(self, path, include_body=True):
        print(f"Attempting to serve: {self.root}/{path}")  # Debugging output
        print(f"Requested path: {path}")  # Log the requested path
        return super().get(path, include_body)

class GetQuestionsHandler(BaseHandler):
    async def get(self): 
        try:
            test_type = self.get_query_argument('testType', None)
            
            query = {"type": test_type} if test_type else {}  # Prepare the query based on the testType

            questions = await db["questions"].find(query).to_list(length=100)
            
            self.write({"questions": [dict(question, _id=str(question["_id"]), questionText=question.get("question", ""), answer=question.get("correctAnswer", "")) for question in questions]})
        except Exception as e:
            self.write({"success": False, "error": str(e)})


class SaveScoreHandler(BaseHandler):
    async def post(self):
        data = json.loads(self.request.body)
        email = data.get("email")
        score_label = data.get("type1")
        score = data.get("score")
        percentage_label = data.get("type2")
        percentage = data.get("percentage")

        update_data = {
            "$set": {
                score_label: score,
                percentage_label: percentage,
            }
        }

        # Mark the test as completed
        if score_label == "Aptitude Test Score":
            update_data["$set"]["has_taken_aptitude"] = True
        elif score_label == "Programming Test Score":
            update_data["$set"]["has_taken_programming"] = True

        await users_collection.update_one({"email": email}, update_data)

        self.write({"success": True})



class jobDetailsHandler(BaseHandler):
    async def get(self):
        try:
            job_details = await db["job_details"].find().to_list(length=100)
            self.write({"success": True, "data": job_details})
        except Exception as e:
            self.write({"success": False, "error": str(e)})
            self.write({"success": False, "error": str(e)})
import io
from bson import ObjectId
class DownloadCVHandler(BaseHandler):
    async def get(self):
        try:
            cv_id = self.get_argument("cv_id", None)
            if not cv_id:
                self.write({"success": False, "error": "CV ID is required."})
            # Ensure user is authenticated
            if not self.get_cookie("admin"):  # Ensure admin is logged in
                self.set_status(403)
                self.write({"success": False, "error": "Unauthorized access"})
                return

            # Validate ObjectId
            try:
                cv_id_obj = ObjectId(cv_id)
            except:
                self.set_status(400)
                self.write({"success": False, "error": "Invalid CV ID"})
                return

            # Retrieve CV from GridFS
            grid_out = await fs.open_download_stream(cv_id_obj)
            file_data = await grid_out.read()
            filename = grid_out.filename if grid_out.filename else "cv.pdf"

            self.set_header("Content-Type", "application/pdf")
            self.set_header("Content-Disposition", f"attachment; filename={filename}")
            self.write(file_data)

        except Exception as e:
            print(f"Error in DownloadCVHandler: {e}")  # Log for debugging
            self.set_status(404)
            self.write({"success": False, "error": "CV not found"})




# New endpoint for deleting questions
class DeleteQuestionHandler(BaseHandler):
    async def post(self):
        try:
            # import pdb; pdb.set_trace()
            data = json.loads(self.request.body)
            question_id = data.get("id")

            if not question_id:
                self.write({"success": False, "error": "Missing question ID"})
                return

            print(f"Attempting to delete question with ID: {question_id}")  # Log the question ID
            print(f"Request body: {data}")  # Log the request body

            result = await db["questions"].delete_one({"_id": ObjectId(question_id)})
            print(f"Delete operation successful: {result.deleted_count} document(s) deleted.")  # Log the result
            print(f"Success: {bool(result.deleted_count)}")  # Log success status

            self.write({"success": bool(result.deleted_count)})
        except Exception as e:
            self.write({"success": False, "error": str(e)})
            print(f"Error during delete operation: {str(e)}")  # Log the error

class PreferredcvHandler(BaseHandler):
    def get(self):
        self.render("preferredcv.html") 

import traceback
import tornado.web
import json


from motor.motor_asyncio import AsyncIOMotorGridFSBucket
fs = AsyncIOMotorGridFSBucket(db)

db = client["testdb"]
users_collection = db["users"]

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
fs = AsyncIOMotorGridFSBucket(db)

class PreferredCVDataHandler(tornado.web.RequestHandler):
    async def get(self):
        try:
            job_id = self.get_argument("job_id", None)  # Fetch job_id from query params
            if not job_id:
                self.write(json.dumps({"success": False, "error": "Job ID is required"}))
                return

            print(f"✅ Received request for preferred CVs for Job ID: {job_id}")

            db1 = client['resumedb']
            job_collection = db['job_Requiremtent_details']
            candidate_collection = db1['skills']
            fs_files_collection = db['fs.files']

            # Fetch job requirements for the specific job_id
            job_reqs = await job_collection.find_one({"job_id": job_id})
            if not job_reqs:
                print("❌ No job requirements found for this Job ID")
                self.write(json.dumps({"success": False, "error": "No job requirements found for given Job ID"}))
                return

            required_skills = set(map(str.strip, (job_reqs.get("keyskills") or "").split(',')))
            print(f"🔎 Required Skills for Job {job_id}: {required_skills}")
            
            matched_candidates = []
            min_match_count = 1  # ✅ Allow at least one skill match
            
            candidates = await candidate_collection.find({}).to_list(None)
            print(f"🔎 Found {len(candidates)} candidates in the database")
            
            for candidate in candidates:
                raw_skills = candidate.get("skills", [])
                
                if isinstance(raw_skills, str):
                    candidate_skills = set(map(str.strip, raw_skills.split(",")))
                elif isinstance(raw_skills, list):
                    candidate_skills = set(raw_skills)
                else:
                    candidate_skills = set()
                
                matching_skills = required_skills.intersection(candidate_skills)
                print(f"📝 Candidate {candidate.get('filename', 'Unknown')} Skills: {candidate_skills} | Matched: {matching_skills}")
                
                if len(matching_skills) >= min_match_count:
                    filename = candidate.get("filename", "").strip()
                    print(f"🔎 Searching for CV in GridFS: '{filename}'")
                    if filename:
                        file_doc = await fs_files_collection.find_one({"filename": filename})
                        if file_doc:
                            cv_id = str(file_doc["_id"])
                            download_link = f"/download_cv?cv_id={cv_id}"
                        else:
                            print(f"❌ CV not found in GridFS for: {filename}")  # Debugging log
                            download_link = f"CV '{filename}' is in the database but could not be found in GridFS."
                    else:
                        print("❌ Missing filename for candidate")  # Debugging log
                        download_link = "No Filename Available"
                    
                    matched_candidates.append({
                        "filename": filename if filename else "Unknown Filename",
                        "download_link": download_link,
                        "matched_skills": list(matching_skills)  # ✅ Include matched skills in response
                    })

            print(f"✅ Sending matched candidates for Job ID {job_id}: {json.dumps(matched_candidates, indent=2)}")
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"success": True, "matched_candidates": matched_candidates}, indent=4))

        except Exception as e:
            print("🔥 ERROR OCCURRED 🔥")
            print("Error Message:", str(e))
            print(traceback.format_exc())  # ✅ Print full traceback
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"success": False, "error": str(e)}))

import json
# Assuming BaseHandler is already defined in this file, remove the unnecessary import
# If BaseHandler is not defined, ensure it is implemented or imported correctly

class CheckTestStatusHandler(BaseHandler):
    async def post(self):
        try:
            if not self.check_authentication():
                print("⚠️ Authentication check failed!")
                self.write({"error": "Unauthorized"})
                return

            data = json.loads(self.request.body)
            email = self.get_current_user()
            print(f"Email retrieved from session: {email}")  # Debugging

            if not email:
                print("⚠️ No email found in session!")
                self.write({"error": "Unauthorized"})
                return

            test_type = data.get("test_type")
            print(f"🔍 Checking test status for {email}, Test Type: {test_type}")

            # Fetch test status from DB
            query = {"email": email}
            if test_type == "aptitude":
                query["has_taken_aptitude"] = True
            elif test_type == "programming":
                query["has_taken_programming"] = True
            else:
                self.write({"error": "Invalid test type"})
                return

            existing_submission = await users_collection.find_one(query)
            print(f"✅ Test Found: {existing_submission}")

            self.write({"taken": bool(existing_submission)})

        except Exception as e:
            print(f"🚨 Error in CheckTestStatusHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal Server Error", "details": str(e)})

    def get_current_user(self):
        user_email = self.get_secure_cookie("user_email")
        if user_email:
            print(f"🔍 Cookie Retrieved: {user_email.decode()}")  # Debugging
            return user_email.decode()
        else:
            print("⚠️ No user_email cookie found.")  # Debugging
            return None

    def check_authentication(self):
        user_email = self.get_secure_cookie("user_email")
        is_authenticated = user_email is not None
        print(f"🔒 Authentication status: {is_authenticated}")  # Debugging
        return is_authenticated
# class GetProgrammingQuestionsHandler(BaseHandler):
#     async def get(self):
#         try:
#             # Fetch programming questions from MongoDB
#             cursor = db["questions"].find({"type": "Coding"})  # Use "Coding" if that's the stored type

#             questions = []
#             async for doc in cursor:
#                 questions.append({
#                     "_id": str(doc.get("_id")),
#                     "question": doc.get("question", ""),
#                     "inputDescription": doc.get("inputDescription", ""),
#                     "outputDescription": doc.get("outputDescription", ""),
#                     "constraints": doc.get("constraints", ""),
#                     "sampleInput": doc.get("sampleInput", ""),
#                     "sampleOutput": doc.get("sampleOutput", ""),
#                     "codeSnippet": doc.get("codeSnippet", ""),
#                     "expectedOutput": doc.get("expectedOutput", ""),
#                     "testCases": doc.get("testCases", [])  # List of dicts with input/output
#                 })

#             self.write({"success": True, "questions": questions})
#         except Exception as e:
#             self.set_status(500)
#             self.write({"success": False, "error": str(e)})


class GetProgrammingQuestionsHandler(BaseHandler):
    async def get(self):
        try:
            cursor = db["questions"].find({"type": "Coding"})

            questions = []
            async for doc in cursor:
                questions.append({
                    "_id": str(doc.get("_id")),
                    "question": doc.get("question", ""),
                    "codeSnippet": doc.get("codeSnippet", "")
                })

            self.write({"success": True, "questions": questions})
        except Exception as e:
            self.set_status(500)
            self.write({"success": False, "error": str(e)})


import json
import httpx  # async HTTP client for API calls
class SubmitProgrammingTestHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            email = data.get("email")
            answers = data.get("answers")  # format: { answer_<qid>: "user predicted output" }

            if not email or not answers:
                self.set_status(400)
                self.write({"success": False, "message": "Missing email or answers"})
                return

            cursor = db["questions"].find({"type": "Coding"})
            correct = 0
            total = 0

            async for q in cursor:
                qid = str(q["_id"])
                key = f"answer_{qid}"

                if key not in answers:
                    continue

                user_output = (answers[key] or "").strip()
                expected_output = (q.get("expectedOutput") or "").strip()

                if user_output == expected_output:
                    correct += 1

                total += 1

            percentage = (correct / total) * 100 if total else 0

            result_data = {
                "score": correct,
                "percentage": round(percentage, 2),
                "answers": answers
            }

            await users_collection.update_one(
                {"email": email},
                {
                    "$set": {
                        "programming_results": result_data,
                        "has_taken_programming": True
                    }
                }
            )

            self.write({"success": True})

        except Exception as e:
            print("❌ Backend error:", e)
            self.set_status(500)
            self.write({"success": False, "message": "Internal Server Error"})

# class GetUserResultHandler(BaseHandler):
#     async def get(self):
#         email = self.get_argument("email", None)
#         if not email:
#             self.set_status(400)
#             self.write({"success": False, "message": "Missing email"})
#             return

#         user = await users_collection.find_one({"email": email})
#         if not user:
#             self.write({"success": False, "message": "User not found"})
#             return

#         user["_id"] = str(user["_id"])
#         self.write({"success": True, "user": user})
from bson import ObjectId

def convert_objectids(doc):
    if isinstance(doc, dict):
        return {k: convert_objectids(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_objectids(i) for i in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc

class GetUserResultHandler(BaseHandler):
    async def get(self):
        email = self.get_argument("email")
        user = await users_collection.find_one({"email": email})
        if not user:
            self.write({"success": False, "message": "User not found"})
        else:
            user = convert_objectids(user)  # ✅ Convert ObjectIds to strings
            self.write({"success": True, "user": user})


class ResultsPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("results.html")  # make sure this file is in your templates folder


import httpx

import json
import httpx
from tornado.web import RequestHandler

class CompileCodeHandler(RequestHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            language_id = data.get("language_id")
            source_code = data.get("source_code")
            stdin = data.get("stdin", "")

            headers = {
                "Content-Type": "application/json",
                "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
                "X-RapidAPI-Key": "c5bd27b786mshdab4e3cbcc47599p184595jsnd2f432513ab7"
            }

            payload = {
                "language_id": language_id,
                "source_code": source_code,
                "stdin": stdin
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=false&wait=true",
                    json=payload,
                    headers=headers
                )

                result = await response.json()  # ✅ Awaited correctly
                self.write(result)

        except Exception as e:
            print("❌ Compile error:", e)
            self.set_status(500)
            self.write({"error": str(e)})





def make_app():
    return tornado.web.Application([
        (r"/", LoginPageHandler),
        (r"/register", RegisterUserHandler),
        (r"/userhome", UserHomePageHandler),
        (r"/adminhome", AdminHomePageHandler),
        (r"/aptitudetest", AptitudeTestHandler),
        (r"/programmingtest", ProgrammingTestHandler),
        (r"/compile", CompileCodeHandler),
        (r"/api/get_programming_questions", GetProgrammingQuestionsHandler),
        (r"/submit_programming_test", SubmitProgrammingTestHandler),  # New endpoint for submitting programming test
        (r"/editprofile", EditProfileHandler),
        (r"/result", ResultsPageHandler),
        (r"/get_user_result", GetUserResultHandler),  # New endpoint for fetching user results
        (r"/get_user_scores", GetUserScoresHandler),  # New endpoint for fetching user scores
        (r"/fetch_user_scores", FetchUserScoresHandler),  # New endpoint for fetching user scores
        (r"/results", ResultsHandler),  # Ensure ResultsHandler is defined
        (r"/auth", AuthHandler),
        (r"/authadmin", AuthAdminHandler),
        (r"/get_questions", GetQuestionsHandler),  # New endpoint for fetching questions
        (r"/add_question", AddQuestionHandler),
        (r"/admintests", AddQuestionHandler),  # Serve the admin tests page directly
        (r"/delete_question", DeleteQuestionHandler),  # New endpoint for deleting questions
        (r"/add_job_details", AddJobDetailsHandler),
        (r'/job_requirements', JobRequirementsHandler),
        (r"/get_questions", GetQuestionsHandler),
        (r"/fetch_sort_listed", FetchSortListedHandler),  # New endpoint for fetching questions
        (r"/save_score", SaveScoreHandler),
        # (r"/cvanalysis", CvHandler),
        (r"/upload-preferred-cv", UploadCVHandler),
        (r"/result", ResultsPageHandler),
        (r"/preferredcv",PreferredcvHandler),
        (r"/preferred_cv_data",PreferredCVDataHandler),
        # (r"/download/?", DownloadCvHandler),  # ✅ New Route for Downloading CVs
        (r"/check_test_status", CheckTestStatusHandler),
        (r"/download_cv/?", DownloadCVHandler),  # New endpoint for fetching questions
        (r"/upload_preferred_cv", UploadPreferredCVPageHandler),
          # Serve the HTML file

        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "templates"}),  # Serve HTML files

        # (r"/(.*)", StaticFileHandler, {"path": "templates"}),  # Serve from current directory

    ], cookie_secret="YOUR_SECRET_KEY", debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(9999)
    print("Server running on http://localhost:9999")
    tornado.ioloop.IOLoop.current().start()
