# University-AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

University-AI is a unified intelligent platform designed to support the entire university ecosystem. Instead of relying on multiple disconnected tools for students, staff, supervisors, and administration, this system brings everything together into one secure, locally hosted solution.

Its purpose is to boost productivity, reduce delays, and provide fast, accurate access to academic and administrative information.

For example:
-Engineering departments usually take 1–2 weeks to review project proposals — but with University-AI, the process can be completed in under one minute.
-Policies & Regulations: Searching through long university policies, rules, and guidelines can take hours. University-AI provides instant answers with clear explanations.

-OJT (On-the-Job Training) Requirements: Students often spend a lot of time trying to understand OJT rules, required documents, company approval steps, and deadlines. University-AI delivers all this information instantly and accurately.

-Administrative Help: Tasks like finding forms, understanding academic probation rules, credit transfer requirements, graduation steps, or registration issues can take a long time. With University-AI, students and staff get immediate support.

-Document Search: Instead of manually looking through PDFs, schedules, notices, and emails, the platform allows fast intelligent search across all university documents.



+ <img width="828" height="388" alt="image" src="https://github.com/user-attachments/assets/e0670604-8ec6-4d17-8835-dcccb3001825" />

This explanation highlights the power of Retrieval-Augmented Generation (RAG) in building secure, high-performance systems that can be hosted locally. As shown in the provided diagram, RAG can be combined with multi-agent architectures to create an automated, intelligent platform capable of handling a wide range of university operations.

By using RAG, we avoid relying on external servers and ensure that all sensitive data remains inside the university’s infrastructure. This allows the system to deliver fast, trustworthy answers based on official documents, policies, OJT guidelines, project requirements, regulations, and more.

Although this project presents the idea at a conceptual level, the university can expand it using more advanced tools for data retrieval, processing, and analysis. With these tools, the system can generate reliable insights, support better decision-making, and help staff and students quickly understand complex information.

In short, RAG + multi-agent systems provide a strong foundation for building a secure, automated, and highly efficient AI platform tailored to the needs of the university.


+how we can run this project?

🚀 How to Run UNI-AI Locally

Follow these steps to set up and run the project on your computer.

1. Create a Virtual Environment (recommended)
python -m venv venv


Activate it:

Windows

venv\Scripts\activate


Linux / macOS

source venv/bin/activate

2. Install Dependencies
pip install -r requirements.txt

3. Run the Application

Navigate to the folder that contains your main app file:

cd UNI-AI


(or whichever directory has your main.py / app.py)

Then start the application:

python main.py

4. Accessing UNI-AI on Your Computer

After running it, the app will show something like:

Running on http://127.0.0.1:8000


Open your browser and enter the URL.

📱 Accessing UNI-AI on Your Phone (Same Wi-Fi)

You can also open the app from your phone while both devices are on the same Wi-Fi network.

Step 1: Find your computer’s IP address

On Windows:

ipconfig


Look for:

IPv4 Address . . . . . : 192.168.x.x

Step 2: Use that IP + Port on your phone

Example:

http://192.168.0.0:8000


Replace the IP and port with your actual values.
Do not forgot to run ollama.

! for more information contact with me in LinkedIn: linkedin.com/in/ya7xa

---

## License

This project is licensed under the MIT License — see the `LICENSE` file for details. (Copyright © 2025 Yahya)


