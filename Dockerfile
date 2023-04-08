# Start with the official Python 3.10 image
FROM python:3.10

# Set an environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED 1

# Create a directory for the application code and set it as the working directory
RUN mkdir /code
WORKDIR /code

# Copy the requirements file to the working directory
COPY requirements.txt /code/

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . /code/

# Expose the port that the application will be running on
EXPOSE 8000

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
