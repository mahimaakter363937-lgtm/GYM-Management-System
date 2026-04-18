🏋️‍♂️ Gym Management System (GMS)
A modern, feature-rich Gym Management System designed to help gym owners manage memberships, diet plans, and workouts seamlessly. This system provides a personalized dashboard for members and a powerful control panel for administrators.



🛠 Tech Stack
The following technologies were used to develop this project:

Backend: Python 3.x, Flask (Web Framework)

Database: * PostgreSQL: For production deployment (e.g., Render, Heroku).

SQLite: For local development and testing.

Frontend: HTML5, CSS3, JavaScript (Bootstrap 5 Framework)

Payment Gateway: Stripe API Integration

Authentication: Werkzeug Security (Password Hashing)



✨ Key Features

👤 Member Features:

Authentication: Secure login and registration system.

Personal Dashboard: View personal profile, gym membership status, and overall progress.

BMI Tracking: Input height and weight to calculate BMI and track fitness levels.

Workout & Diet Plans: Access custom diet and workout charts assigned by the admin.

Notifications: Real-time alerts for membership expiry and payment status updates.



🔑 Admin Features:

Admin Dashboard: A comprehensive overview of total members, active plans, and generated revenue.

Member Management: Easily add, edit, or remove members from the system.

Attendance System: Track and record the daily attendance of gym members.

Plan Assignment: Create and assign personalized diet plans and workout schedules.

Feedback Handling: Review and seamlessly reply to member complaints or feedback.



🔐 Environment Variables (.env setup)
To keep sensitive data secure, this project uses environment variables. Before running the application, create a .env file in the root directory and configure the following keys:

Code snippet
# Flask Configuration
FLASK_SECRET_KEY=your_super_secret_key_here

# Database Configuration (For PostgreSQL deployment)
# Leave empty for local SQLite usage
DATABASE_URL=postgres://username:password@host:port/database_name

# Stripe Payment Gateway
STRIPE_PUBLIC_KEY=pk_test_your_public_key
STRIPE_SECRET_KEY=sk_test_your_secret_key

<img width="659" height="596" alt="image" src="https://github.com/user-attachments/assets/ba664c25-1dc6-432e-9613-cbde110487cd" />

<img width="1868" height="890" alt="image" src="https://github.com/user-attachments/assets/f10c5061-8bae-4dd7-ac32-70464f57bdc9" />

<img width="1918" height="836" alt="image" src="https://github.com/user-attachments/assets/a6cfd32f-d0ab-4593-9b43-878af4505f91" />

<img width="1891" height="895" alt="image" src="https://github.com/user-attachments/assets/fd027a2d-f556-4a7c-a1df-4598d5e9fb94" />

<img width="1856" height="874" alt="image" src="https://github.com/user-attachments/assets/e616c542-ab6c-4964-9b38-74f5f94136d1" />

<img width="1743" height="791" alt="image" src="https://github.com/user-attachments/assets/febc61a9-1264-4ea1-85f7-6e6b784d6353" />

<img width="1833" height="854" alt="image" src="https://github.com/user-attachments/assets/fbb70ee4-c4e4-4f3b-912d-8b1595c1629f" />

<img width="1843" height="798" alt="image" src="https://github.com/user-attachments/assets/8f9fdb80-8dc1-457d-a2d1-5c254be37090" />

<img width="1816" height="840" alt="image" src="https://github.com/user-attachments/assets/227cc0f8-e602-4a6b-a509-a01092187ced" />

<img width="672" height="644" alt="image" src="https://github.com/user-attachments/assets/71b1739b-9eed-4075-b694-a064e112baf8" />

<img width="1833" height="833" alt="image" src="https://github.com/user-attachments/assets/5b189fb9-6581-4739-a60c-839e338bdaf0" />

<img width="1860" height="823" alt="image" src="https://github.com/user-attachments/assets/df84bdf7-bf0a-4449-a0d5-e6a184ae4f6e" />


## 👥 Contributors (Group 09)
This project was developed as an academic Capstone Project for the course Software Engineering Design Capstone Project (SE-331)

* **Mithila Islam Richy** (ID: 0242310005341355): Responsible for personal fitness profile management, member management, workout scheduling, and attendance management.
* **Mahima Akter Aughtay** (ID: 0242310005341415): Responsible for personal profile management, membership plan management, diet plan assignment, and workout & diet plan updates.
* **Mohosina Banu Biva** (ID: 232-35-612): Responsible for membership plan selection, Stripe payment integration, progress tracking dashboard, and workout & diet views.
* **Zayed Bin Siddik** (ID: 0242310005341037): Responsible for membership status management, payment history & status display, the notification system, and feedback handling.

