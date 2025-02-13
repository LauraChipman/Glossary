from flask import Flask, render_template, request, redirect, url_for, send_file, abort
from pymongo import MongoClient
import gridfs 
from gridfs import GridFS
from bson.objectid import ObjectId
from flask import jsonify
import base64
import os
import secrets
from flask import flash
from datetime import datetime


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generates a 32-character hexadecimal string

app.config['UPLOAD_FOLDER'] = 'static/images'

# MongoDB connection setup
client = MongoClient("mongodb+srv://glossary_user:QSVZTxNNsazC2nrK@serverlessinstance0.g4zurmd.mongodb.net/?retryWrites=true&w=majority&appName=ServerlessInstance0")
db = client['GlossaryDB']
collection = db['GlossaryEntries']
fs = GridFS(db)  # Initialize GridFS for file sto

from bson import ObjectId

@app.route('/')
def index():
    # Convert `definition` field from list to string if necessary
    glossary_entries = collection.find({"definition": {"$type": "array"}})
    for entry in glossary_entries:
        definition_string = ''.join(entry['definition'])
        collection.update_one(
            {"_id": entry["_id"]},
            {"$set": {"definition": definition_string}}
        )

    # Query MongoDB for all entries in the collection
    glossary_entries = list(collection.find())

    # Collect unique tags from all entries
    all_tags = set()
    for entry in glossary_entries:
        for tag in entry.get("tags", []):
            all_tags.add(tag)
    all_tags = sorted(list(all_tags))  # Sort tags alphabetically

    # Group entries by the first letter of the title
    glossary_data = {}
    for entry in glossary_entries:
        title = entry.get('title', '').strip()
        first_letter = title[0].upper() if title else 'Unknown'
        if first_letter not in glossary_data:
            glossary_data[first_letter] = []

        glossary_data[first_letter].append({
            "_id": str(entry["_id"]),
            "title": title,
            "definition": entry.get('definition', ''),
            "is_html": entry.get('is_html', True),
            "link": entry.get('link', ''),
            "image_ids": entry.get('image_ids', []),
            "tags": entry.get('tags', [])
        })

    # Sort glossary data by letter and by title within each group
    sorted_glossary = {
        letter: sorted(entries, key=lambda e: e.get('title', ''))
        for letter, entries in sorted(glossary_data.items())
    }

        # Glossary statistics
    total_entries = collection.count_documents({})

    # Fetch the most recent entry (by created_at) and most recent edit (by updated_at)
    most_recent_entry = list(collection.find().sort("created_at", -1).limit(1))
    most_recent_edit = list(collection.find().sort("updated_at", -1).limit(1))

     # Extract title fields and IDs for the most recent additions and edits, if available
    recent_entry_title = most_recent_entry[0]["title"] if most_recent_entry else "N/A"
    recent_entry_id = str(most_recent_entry[0]["_id"]) if most_recent_entry else None

    recent_edit_title = most_recent_edit[0]["title"] if most_recent_edit else "N/A"
    recent_edit_id = str(most_recent_edit[0]["_id"]) if most_recent_edit else None

    # Render the template with sorted glossary data, unique tags, and stats
    return render_template(
        'interactive_glossary_template.html',
        glossary=sorted_glossary,
        all_tags=all_tags,
        total_entries=total_entries,
        recent_entry_title=recent_entry_title,
        recent_entry_id=recent_entry_id,
        recent_edit_title=recent_edit_title,
        recent_edit_id=recent_edit_id
    )



@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    print("Add entry route accessed") 
    if request.method == 'POST':
        # Get data from form submission
        new_title = request.form['title']
        new_definition = request.form['definition']
        is_html = request.form['is_html'] == 'True' 

        # Get tags from the form and split them into an array
        tags_input = request.form.get("tags")  # E.g., "OOP, Java, Security"
        tags = tags_input.split(",") if tags_input else []  # Split tags by comma
        tags = [tag.strip() for tag in tags]  # Trim whitespace around each tag

        # Handle multiple images
        images = request.files.getlist('images[]') 
        print("Files received:", [img.filename for img in images]) # Expecting multiple files
        image_ids = []
        for image in images:
            if image and image.filename:
                print(f"Uploading image: {image.filename}")
                image_id = fs.put(image, filename=image.filename, content_type=image.content_type)
                image_ids.append(str(image_id))  # Add each image ID to the list
                print(f"Image uploaded with ID: {image_id}")
        # Handle the URL link
        link = request.form.get('link')
        if link:
            # Add protocol if the URL starts with "www."
            if link.startswith('www.'):
                link = 'https://' + link
            # Ensure the link has http:// or https://
            elif not link.startswith(('http://', 'https://')):
                link = 'https://' + link

        # Insert the new entry into MongoDB with image_ids as a list
        new_entry_id = collection.insert_one({
            "title": new_title,
            "definition": new_definition,
            "link": link,
            "is_html": is_html,
            "image_ids": image_ids,  # Store list of image IDs instead of a single ID
            "tags": tags,
            "created_at": datetime.utcnow(),  # Set the creation timestamp
            "updated_at": datetime.utcnow()   # Set the initial updated timestamp
        }).inserted_id  # Save the new entry ID

        flash('Entry added successfully!', 'success')
        return redirect(url_for('index', entry_id=str(new_entry_id)))  # Redirect to the new entry page
    
        print("Form Data:", request.form)

        print(f"Image IDs saved for entry '{new_title}': {image_ids}")

        return redirect(url_for('index'))

    return render_template('add_entry.html')


@app.route('/edit_entry/<title>', methods=['GET', 'POST'])
def edit_entry(title):
    # Fetch the entry from MongoDB based on title
    entry = collection.find_one({"title": title})

    if request.method == 'POST':
        # Get updated data from the form
        new_title = request.form['title']
        new_definition = request.form['definition']
        tags_input = request.form.get("tags")
        is_html = request.form['is_html'] == 'True'
        updated_tags = tags_input.split(",") if tags_input else []
        updated_tags = [tag.strip() for tag in updated_tags]

        # Debugging: Print existing images to verify retrieval
        print(f"Existing image IDs before update: {entry.get('image_ids', [])}")

        # Update or add images
        images = request.files.getlist('images[]')
        image_ids = entry.get("image_ids", [])  # Retrieve existing image_ids or start with an empty list

        # Handle new image uploads if provided
        for image in images:
            if image.filename:  # Check if an image is provided
                image_id = fs.put(image, filename=image.filename, content_type=image.content_type)
                image_ids.append(str(image_id))  # Add each new image ID to the list
                print(f"Uploaded new image with ID: {image_id}")

        # Check if there are images selected for deletion
        delete_image_ids = request.form.getlist('delete_images')
        for image_id in delete_image_ids:
            if image_id in image_ids:
                fs.delete(ObjectId(image_id))  # Delete the image from GridFS
                image_ids.remove(image_id)  # Remove the ID from the list
                print(f"Deleted image with ID: {image_id}")

        # Handle the URL link with protocol check
        new_link = request.form.get('link', entry.get('link', ''))
        if new_link:
            if new_link.startswith('www.'):
                new_link = 'http://' + new_link
            elif not new_link.startswith(('http://', 'https://')):
                new_link = 'http://' + new_link

        # Prepare the updated document
        updated_entry = {
            "title": new_title,
            "definition": [new_definition],  # Store as a list to match MongoDB schema
            "link": new_link,
            "is_html": is_html,
            "image_ids": image_ids,  # Store list of image IDs instead of a single image ID
            "tags": updated_tags,
            "updated_at": datetime.utcnow()  # Update the modification timestamp
        }
        collection.update_one({"title": title}, {"$set": updated_entry})

        flash('Entry updated successfully!', 'success')
        return redirect(url_for('index', entry_id=str(entry["_id"])))  # Redirect to the updated entry page

    return render_template('edit_entry.html', entry=entry)


@app.route('/images', methods=['POST'])
def get_images():
    image_ids = request.json.get('image_ids', [])
    images = []

    for image_id in image_ids:
        try:
            # Retrieve each image file from GridFS
            image_file = fs.get(ObjectId(image_id))
            
            # Encode the image data to base64
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            images.append({
                "image_id": image_id,
                "content_type": image_file.content_type,
                "data": f"data:{image_file.content_type};base64,{image_data}"
            })
        
        except gridfs.errors.NoFile:
            print(f"No file found in GridFS for image_id: {image_id}")
            images.append({
                "image_id": image_id,
                "error": "File not found"
            })
        
        except Exception as e:
            print(f"An error occurred for image_id {image_id}: {e}")
            images.append({
                "image_id": image_id,
                "error": str(e)
            })

    # Return all images in JSON format
    return jsonify(images)

@app.route('/image/<image_id>')
def get_image(image_id):
    try:
        # Attempt to retrieve the image file from GridFS
        image_file = fs.get(ObjectId(image_id))
        
        # Send the file with its associated MIME type
        return send_file(image_file, mimetype=image_file.content_type)
    except gridfs.errors.NoFile:
        # Log an error message (optional) for debugging purposes
        print(f"No file found in GridFS for image_id: {image_id}")
        
        # Return a 404 error if the image does not exist in GridFS
        abort(404)

    except Exception as e:
        # Log any other exceptions that might occur
        print(f"An error occurred: {e}")
                # Return a 500 error for general failures
        abort(500)

@app.route('/delete_entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    print(f"Attempting to delete entry with ID: {entry_id}")
    try:
        # Attempt to delete the entry with the given ID
        result = collection.delete_one({'_id': ObjectId(entry_id)})
        if result.deleted_count > 0:
            flash('Entry deleted successfully!', 'success')
            return '', 204  # Success, no content to return
        else:
            print(f"No entry found with ID: {entry_id}")
            return '', 404  # Not found
    except Exception as e:
        print(f"Error deleting entry: {e}")  # Log any errors
        return '', 500  # Internal server error


    # Redirect to the main glossary page after deletion
    return redirect(url_for('index'))

from bson import ObjectId
from flask import render_template, jsonify, abort

@app.route('/entry/<entry_id>')
def entry_page(entry_id):
    # Find the entry by ID in the database
    entry = collection.find_one({"_id": ObjectId(entry_id)})
    if not entry:
        # If the entry is not found, return a 404 error
        abort(404, description="Entry not found")

    # Pass the entry data to the template
    return render_template('entry_page.html', entry=entry)


if __name__ == "__main__":
    app.run(debug=True)


