# Create a ubuntu base image with python 3 installed
FROM python:3.9.9

# Set the working directory
WORKDIR /

# Copy all the files
COPY . .

# Install dependencies
RUN apt-get -y update
RUN apt-get update

RUN pip install --upgrade pip
RUN apt-get install -y python3 python3-pip
# RUN pip3 install -r requirements.txt
RUN pip install flask
# RUN pip install allosaurus
RUN pip3 install --no-cache-dir torch==1.10.1
RUN pip3 install --no-cache-dir allosaurus
RUN pip install -U flask-cors

# Enter entry point parameters executing the container
# ENTRYPOINT ["python", "./main.py"] 
ENTRYPOINT ["python", "./app.py"] 

# Expose the required port
EXPOSE 5000

#Run the command
# CMD gunicorn main:app