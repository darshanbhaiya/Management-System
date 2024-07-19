  # Import the SQLAlchemy database object
from app import db,app
from app import Users  # Import the Users model
 

# Define the new user values for each designation
with app.app_context():
    new_users = [
        
        {
            'User_ID': '1',
            'User_fullname': 'Admin',
            'User_Address': '789 Oak St, City',
            'User_phone': '5551234567',
            'User_email': 'admin@example.com',
            'User_password': 'admin',
            'UserName': 'admin',
            'User_Designation': 'Admin'
        },
        # Add more new users as needed
        {
            'User_ID': '3',
            'User_fullname': 'John Doe',
            'User_Address': '123 Main St, City',
            'User_phone': '1234567890',
            'User_email': 'john@example.com',
            'User_password': 'password1',
            'UserName': 'john_doe',
            'User_Designation': 'Production Manager'
        },
        {
            'User_ID': '2',
            'User_fullname': 'Jane Smith',
            'User_Address': '456 Elm St, City',
            'User_phone': '9876543210',
            'User_email': 'jane@example.com',
            'User_password': 'password2',
            'UserName': 'jane_smith',
            'User_Designation': 'Delivery Person'
        },
    ]

    # Insert new users into the database
    for user_data in new_users:
        new_user = Users(**user_data)
        db.session.add(new_user)

    # Commit the changes to the database
    db.session.commit()

    print("New users added successfully.")