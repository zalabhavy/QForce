## Fork the Repository

First, fork the repository to your GitHub account. This creates a copy of the repository under your username.

1. Go to the project repository page on GitHub.
2. Click on the "Fork" button at the top-right of the page.
3. Wait for the repository to be copied to your GitHub account.

## Clone the Repository to Your Local Machine

After forking the repository, clone it to your local machine using the following command:

```bash
git clone https://github.com/<yourusername>/QForce
```

```bash
cd QForce
```

## 1. Create a Virtual Environment
First, navigate to your project directory and run the following command to create a virtual environment

```bash
python3 -m venv venv
```

## 2. Activate the Virtual Environment
Activate the virtual environment by running:

  ```bash
source venv/bin/activate
```

## 3. Install Project Dependencies
Now that your virtual environment is activated, install the required dependencies:

```bash
pip install flask pandas networkx folium geopy openpyxl
```

## 4. Run the Application
After installing the dependencies, you can run the Flask application with:

```bash
python app.py
```

<img width="1069" alt="image" src="https://github.com/user-attachments/assets/796f62d0-57e9-4cf5-8b01-85602a6b27aa" />



