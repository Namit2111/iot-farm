from flask import *
import re
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import requests
import json
import os
import datetime
from flask_cors import CORS
# initialize first flask
app = Flask(__name__, static_folder='static',template_folder="templates")
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/Project'
#   # Replace with your MongoDB connection URI
app.config['MONGO_URI'] = "mongodb+srv://coe211153csecoe:AZmtosHqknPrbcI2@cluster0.mhxrfuv.mongodb.net/Project?retryWrites=true&w=majority"
mongo = PyMongo(app)
CORS(app)
secret_key = os.urandom(24)
app.secret_key = secret_key

@app.route("/")
def home():
    # Check if the user is logged in
    if 'user_id' in session:
        # Retrieve the user's information from the database
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})

        if user:
            # Get the username from the user's information
            username = user["username"]
            privlidge = user.get('privlidge')

            if 'profile_image' in user:

                return render_template("home.html", username=username, privlidge=privlidge,profile_pic=user['profile_image'])
            # Render the home template with the logged-in username
            return render_template("home.html", username=username, privlidge=privlidge)

    # Render the home template without the username
    return render_template("home.html")



# Sign up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        privlidge = "user"

        # Validate the form data (add more validation if needed)
        if not re.match(r'^\w+$', username):
            return "Invalid username. Username should only contain alphanumeric characters and underscores."

        # Check if the username already exists in the database
        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            return "Username already exists. Please choose a different username."

        # Insert the new user into the database
        mongo.db.users.insert_one({
            'username': username,
            'password': password,
            'email': email,
            'phone': phone,
            'privlidge': privlidge,
            
        })

        # Redirect to the login page or any other desired page
        return redirect('/login')

    # Render the sign-up form
    return render_template('register.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form data
		
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username and password match a user in the database
        user = mongo.db.users.find_one({'username': username, 'password': password})
        
        if user:
            session['user_id'] = str(user['_id'])
            username = user["username"]
            if user["privlidge"] == "admin":
                return redirect(url_for('admin'))
            # Store the user's information in the session
            
            
            # Redirect to the home page or any other desired page
            return redirect(url_for('user_dashboard'))
        else:
            return "Invalid username or password."
    
    # Render the login form
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()

    # Redirect to the desired page after logout (e.g., login or home)
    return redirect(url_for('home'))


@app.route('/admin')
def admin():
    # Check if the user has admin privileges
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        if user and user.get('privlidge') == 'admin':
            # Retrieve all users from the database
            users = mongo.db.users.find()

            # Get a list of user names and profile images
            user_data = []
            for user in users:
                if user['privlidge'] != 'admin':
                    username = user['username']
                    
                    profile_image = user.get('profile_image')
                    if profile_image is None:
                        # If user doesn't have a profile image, set a default image URL or None
                        profile_image = None  # Replace with default image URL if desired
                    user_data.append({'username': username, 'profile_image': profile_image})

            # Render the admin template with the list of user names and profile images
            return render_template('admin.html', user_data=user_data)

    # Redirect to the home page or any other desired page
    return redirect(url_for('home'))



@app.route("/admin/user_details/<username>")
def user_details(username):
    # Check if the user has admin privileges
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user and user.get('privlidge') == 'admin':
          
            # Retrieve the user details from the database based on the username
            user_details = mongo.db.users.find_one({'username': username})
            if user_details:
                
                # Check if the user has an API key
                if 'api_key' in user_details:
                    
                    api_key = user_details['api_key']
                    # Make a request to the API using the API key
                    try:
                        response = requests.get(api_key)
                       
                        response.raise_for_status()
                        data = response.json()
                        # Extract the required data from the API response
                        channel_name = data["channel"]["name"]
                        feeds = data["feeds"]
                        # Rename the field names
                        renamed_feeds = []
                        for feed in feeds:
                            renamed_feed = {
                                "created_at": feed["created_at"],
                                "entry_id": feed["entry_id"],
                                "soil_moisture": feed["field1"],
                                "humidity": feed["field2"],
                                "temperature": feed["field3"]
                            
                                
                            }
                            renamed_feeds.append(renamed_feed)
                        cc=[]
                        crop=[]
                        if "chemical_name" in user_details:
                            cc =[{"chemial":user_details['chemical_name'],
                            "date":user_details['date']}] 
                        duser = [{"email":user_details['email'],"phone":user_details["phone"]}]
                        if "crop" in user_details:
                            crop = {"crop":user_details['crop']}

                        crop_data = []
                    # Retrieve the crop data from the farm collection based on the user and selected crop
                        crop_entries = mongo.db.farm.find({'user_id': str(user_details['_id'])})
                        
                
                        crop_data = list(crop_entries)
                        area=[]
                        if "area" in user_details:
                            area = user_details['area']
                       
                        # Render the user_details template with the API data and user details
                        return render_template('user_details.html',area=area, user_details=user_details, channel_name=channel_name, feeds=renamed_feeds,chemical=cc,crop = crop,duser=duser,crop_data=crop_data)
                    except requests.exceptions.RequestException:
                        
                        # Handle the request exception
                        error_message = "Failed to retrieve data from the API."
                        return render_template('user_details.html', user_details=user_details, error_message=error_message)

                # Render the user_details template with the user details
                return render_template('user_details.html', user_details=user_details)
            else:
                return "User not found"
    # Redirect to the home page or any other desired page
    return redirect(url_for('home'))

@app.route("/delete_user/<username>", methods=["POST"])
def delete_user(username):
    # Check if the user has admin privileges
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user and user.get('privlidge') == 'admin':
            # Delete the user from the database based on the username
            mongo.db.users.delete_one({'username': username})

            # Redirect to the admin page after successful deletion
            return redirect(url_for('admin'))

    # Redirect to the home page or any other desired page if the user doesn't have admin privileges
    return redirect(url_for('home'))

@app.route("/panel", methods=['GET', 'POST'])
def panel():
    # Check if the user has logged in
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            # Check if the user has an API key field
            if 'api_key' not in user:
                # API key field is missing, ask the user for an API key
                return render_template("ask_api_key.html")

            # Retrieve the API key for the user
            api_key = user['api_key']

            # Make the API request using the retrieved API key
            response = requests.get(api_key)
            
            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the response content as JSON
                data = json.loads(response.content)
                
                # Extract the required data from the response
                channel_name = data["channel"]["name"]
                feeds = data["feeds"]
               
                
                # Rename the field names
                renamed_feeds = []
                for feed in feeds:
                    renamed_feed = {
                        "created_at": feed["created_at"],
                        "entry_id": feed["entry_id"],
                        "soil_moisture": feed["field1"],
                        "humidity": feed["field2"],
                        "temperature": feed["field3"]
                    }
                    renamed_feeds.append(renamed_feed)
                
                if "chemical_name" in user:
                    cc = [{
                        "chemical": user["chemical_name"],
                        "date": user['date']
                    }]
                else:
                    cc = []
                
                crop_data = []
                    # Retrieve the crop data from the farm collection based on the user and selected crop
                crop_entries = mongo.db.farm.find({'user_id': session['user_id']})
                
                crop_data = list(crop_entries)

                

                with open('static/crop_data.json', 'r') as file:
                    new_crop_data = json.load(file)

                # Get all crop names from the loaded data
                all_crops = list(new_crop_data.keys())

                area = []
                if "area" in user:
                    area = user['area']
                
                # Render the panel template and pass the data
                return render_template("user_panel.html",
                                       username=user["username"],
                                       channel_name=channel_name,
                                       feeds=renamed_feeds,
                                       chemical=cc,
                                       crop_data=crop_data,
                                       crops=all_crops,
                                       area = area)
               
            else:
                # Request was not successful, handle the error
                return "Error occurred: " + response.text
    
    # User is not logged in or API key field is missing, redirect to the home page or any desired page
    return redirect(url_for('home'))



@app.route('/save_api_key', methods=['POST'])
def save_api_key():
    # Get the API key from the form data
    api_key = request.form['api_key']
    base_api = "https://api.thingspeak.com/channels/{}/feeds.json?resuls=2".format(api_key)
    try:
        # response = requests.get(api_key)
        response = requests.get(base_api)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
    except requests.exceptions.RequestException:
        # Handle the request exception
        error_message = "Invalid API key. Please enter a valid API key."
        return render_template("ask_api_key.html", error_message=error_message)
    


    # Check if the user is logged in
    if 'user_id' in session:
        # Update the user's API key in the database
        user_id = session['user_id']
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'api_key': base_api}})
        return redirect(url_for('user_dashboard'))
    
    return redirect(url_for('home'))



# adding chemical data api
@app.route('/add-chemical', methods=['POST'])
def add_chemical():
    chemical_name = request.form['chemical-name']
    date = request.form['date']

    # Insert data into MongoDB
    if 'user_id' in session:
        user_id = session['user_id']
        chemical_data = {
            'user_id': user_id,
            'chemical': chemical_name,
            'chemical_date': date
        }
        mongo.db.farm.insert_one(chemical_data)

        return redirect(url_for('panel'))

    
        #return redirect(url_for('panel'))

        

@app.route('/user-profile', methods=['POST','GET'])
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        user =mongo.db.users.find_one({'_id': ObjectId(user_id)})
        
        if request.method =='POST' and 'image' in request.files:
            images = request.files.getlist('image')
            if len(images)>0:
                username = user['username']
                user_dir = 'user_images/'+username
                image_paths = []
                for image in images:
                    if image.filename!= "":
                        filename = image.filename
                       
                        image_path = user_dir
                        image_path = image_path+"/"+filename
                        
                        if not os.path.exists("static/"+user_dir):
                            os.makedirs("static/"+user_dir)
                        image.save("static/"+image_path)
                        image_paths.append(image_path)


                mongo.db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$push': {'gallery': {'$each': image_paths}}}
                )
                return "Image save successfully"






        if "profile_image" in user:
            if "gallery" in user:
                return render_template('user_profile.html', feed={"name":user['username'],'email':user['email'],"phone":user['phone'],"pic":user['profile_image'],"gallery": user['gallery']})    
            else:
                return render_template('user_profile.html', feed={"name":user['username'],'email':user['email'],"phone":user['phone'],"pic":user['profile_image']})
        if "gallery" in user:
            return render_template('user_profile.html', feed={"name":user['username'],'email':user['email'],"phone":user['phone'],"gallery": user['gallery']})
        
        return render_template('user_profile.html', feed={"name":user['username'],'email':user['email'],"phone":user['phone']})
    else:
        # Handle the case when the user is not logged in or user_id is missing from session
        return "User not authenticated"



@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

        if request.method == 'POST':
            # Update user data with the form values submitted
            updated_user = {
                'username': request.form.get('name'),
                'phone': request.form.get('phone'),
                'email': request.form.get('email')
            }

            # Update the user data in the database
            mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': updated_user})
            if 'profile_image' in request.files:
                profile_image = request.files['profile_image']
                filename= updated_user['username']+".jpg"
                profile_image.save('static/profile/{}'.format(filename))
                updated_user['profile_image'] = "profile/"+filename
            mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': updated_user})
            # Redirect to the profile page after editing
            return redirect('/user-profile')
        else:
            return render_template('edit_profile.html', user=user)
    else:
        # Handle the case when the user is not logged in or user_id is missing from session
        return "User not authenticated"


@app.route('/crop_data/<crop_name>')
def get_crop_data(crop_name):
    with open('static/crop_data.json', 'r') as file:
       
        crop_data = json.load(file)
        print(crop_data)
    if crop_name in crop_data:
        return jsonify(crop_data[crop_name])
    else:
        return jsonify({'error': 'Crop not found'})



@app.route('/update_crop', methods=['POST'])
def update_crop():
    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

        if user:
            # Get the selected crop from the form data
            selected_crop = request.form.get('crop_name')

            # Update the user document with the selected crop
            mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$push': {'crops': selected_crop}})

            # Get the current date
            today = datetime.date.today()

            # Update the farm collection with the user's farm-related data
            farm_data = {
                'user_id': user_id,
                'crop': selected_crop,
                'date': today.isoformat(),
                # Add more farm-related data fields as needed
            }
            mongo.db.farm.insert_one(farm_data)

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'User not found'})
    else:
        # Handle the case when the user is not logged in or user_id is missing from session
        return jsonify({'success': False, 'error': 'User not authenticated'})






@app.route('/edit_user_as_admin/<username>', methods=['GET', 'POST'])
def edit_user_as_admin(username):
    if 'user_id' in session:
        admin_id = session['user_id']
        admin = mongo.db.users.find_one({'_id': ObjectId(admin_id)})

        # Check if the admin has admin privileges
        if 'privlidge' in admin and admin['privlidge'] == 'admin':
            user = mongo.db.users.find_one({'username': username})

            if user:
                if request.method == 'POST':
                    # Update user data with the form values submitted
                    updated_user = {
                        'username': request.form.get('name'),
                        'phone': request.form.get('phone'),
                        'email': request.form.get('email'),
                        'crop': request.form.get('crop')
                    }

                    # Update the user data in the database
                    
                    mongo.db.users.update_one({'_id': user['_id']}, {'$set': updated_user})
                    username = mongo.db.users.find_one({'_id': ObjectId(user['_id'])})
                    if 'profile_image' in request.files:
                        profile_image = request.files['profile_image']
                        # profile_image.save('/path/to/save/image.jpg')

                    # Redirect to the user details page after editing
                    return redirect(url_for('user_details', username=username['username']))
                else:
                    return render_template('edit_profile_as_admin.html', user=user)
            else:
                # Handle the case when the user does not exist
                return "User not found."
        else:
            # Handle the case when the admin does not have admin privileges
            return "You are not authorized to edit user profiles as an admin."
    else:
        # Handle the case when the user is not logged in or user_id is missing from session
        return "User not authenticated"



# Route to display and update crops for admin
@app.route('/all_crop', methods=['GET', 'POST'])
def all_crop():
    # Check if the user is logged in and has admin privileges
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user and user.get('privlidge') == 'admin':
            if request.method == 'POST':










                if 'delete_crop' in request.form:
                    crop_to_delete = request.form['delete_crop']
                    
                    # Load existing crop data from crop_data.json
                    with open('static/crop_data.json', 'r') as file:
                        crop_data = json.load(file)
                    
                    # Delete the crop from the crop_data dictionary
                    if crop_to_delete in crop_data:
                        del crop_data[crop_to_delete]
                    
                    # Save the updated crop data back to crop_data.json
                    with open('static/crop_data.json', 'w') as file:
                        json.dump(crop_data, file, indent=4)
                    
                    return redirect('/all_crop')
                # Get the submitted form data
                new_crop_name = request.form['new_crop_name']
                new_sowing_time = request.form['new_sowing_time']
                new_harvesting_time = request.form['new_harvesting_time']
                new_suitable_temperature = request.form['new_suitable_temperature']
                new_climate = request.form['new_climate']
                new_soil = request.form['new_soil']
                new_fertilizer = request.form['new_fertilizer']
                new_soil_moisture = request.form['new_soil_moisture']

                # Load existing crop data from crop_data.json
                with open('static/crop_data.json', 'r') as file:
                    crop_data = json.load(file)

                # Add the new crop to the crop_data dictionary
                crop_data[new_crop_name] = {
                    "Sowing time": new_sowing_time,
                    "Harvesting time": new_harvesting_time,
                    "Suitable temperature": new_suitable_temperature,
                    "Climate": new_climate,
                    "Soil": new_soil,
                    "Fertilizer": new_fertilizer,
                    "Soil moisture": new_soil_moisture
                }

                # Save the updated crop data back to crop_data.json
                with open('static/crop_data.json', 'w') as file:
                    json.dump(crop_data, file, indent=4)

                return redirect('/all_crop')

            else:
                # Load existing crop data from crop_data.json
                with open('static/crop_data.json', 'r') as file:
                    crop_data = json.load(file)

                return render_template('all_crop.html', crop_data=crop_data)

        else:
            return "Access Denied"
    else:
        return redirect('/login')




@app.route("/user-dashboard")
def user_dashboard():
    return render_template("user_dashboard.html")




@app.route('/add-yield', methods=['POST'])
def add_yield():
    if 'user_id' in session:
        user_id = session['user_id']
        yield_crop = request.form['yield-crop']
        date = request.form['yield-date']

        # Insert data into MongoDB
        yield_data = {
            'user_id': user_id,
            'yield_crop': yield_crop,
            'yield_date': date
            # Add more fields as needed
        }
        mongo.db.farm.insert_one(yield_data)

        return redirect(url_for('panel'))
    else:
        return redirect(url_for('home'))




from flask import jsonify

@app.route("/chart-data", methods=['GET'])
def chart_data():
    # Check if the user has logged in
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            # Check if the user has an API key field
            if 'api_key' not in user:
                # API key field is missing, return an error response
                return jsonify({'error': 'API key is missing'})

            # Retrieve the API key for the user
            api_key = user['api_key']

            # Make the API request using the retrieved API key
            response = requests.get(api_key)

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the response content as JSON
                data = json.loads(response.content)

                # Extract the required data from the response
                feeds = data["feeds"]
                
                # Rename the field names
                renamed_feeds = []
                for feed in feeds:
                    renamed_feed = {
                        "created_at": feed["created_at"],
                        "entry_id": feed["entry_id"],
                        "soil_moisture": feed["field1"],
                        "humidity": feed["field2"],
                        "temperature": feed["field3"]
                    }
                    renamed_feeds.append(renamed_feed)
              
                # Return the feeds data as a JSON response
                return jsonify(renamed_feeds)

            else:
                # Request was not successful, return an error response
                return jsonify({'error': 'API request failed'})

    # User is not logged in or API key field is missing, return an error response
    return jsonify({'error': 'User not logged in or API key is missing'})


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Check if the user is logged in and has admin privileges
        if 'user_id' in session:
            user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
            if user and user.get('privlidge') == 'admin':
                # Get the form data
                api_key = None
                username = request.form['username']
                password = request.form['password']
                email = request.form['email']
                contact = request.form['contact']
                role = request.form['role']

                # Perform additional validation or processing if needed

                # Example: Save the user data to the database
                user_data = {
                    'username': username,
                    'password': password,
                    'email': email,
                    'phone': contact,
                    'privlidge': role
                }
                mongo.db.users.insert_one(user_data)

                # Redirect to a success page or any other desired route
                return "Successfully added"
            else:
                return "Access Denied"
        else:
            return redirect('/login')  # Redirect to login page if user is not logged in

    # If the request method is GET, render the add_user.html template
    return render_template('add_user.html')


@app.route('/area', methods=['POST'])
def area():
    if 'user_id' in session:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            # Retrieve the length and breadth values from the request form
            length = float(request.form['length'])
            breadth = float(request.form['breadth'])
            
            # Calculate the area
            area = length * breadth
            
            # Save the area in the user collection
            user['area'] = area
            mongo.db.users.update_one({'_id': user['_id']}, {'$set': user})
            
            # Redirect to a success page or any other desired route
            return redirect('/user-dashboard')
        else:
            return "Access Denied"
    else:
        return redirect('/login')  # Redirect to login page if user is not logged in




# run code in debug mode
if __name__== "__main__":
    app.run(host='0.0.0.0',port=5000,use_reloader=True,debug=True)
