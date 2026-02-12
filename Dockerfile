#The base image to start from, exact version of our python in our app. slim - minimal linux image(smaller size,fast build)
FROM python:3.12-slim

#sets the default working directory inside the container. 
#/expense_image - path inside the container ecosystem.
WORKDIR /expense_image

#copies requriements.txt from host machine to the image. . means current directory of the image which is /expense_image.
COPY requirements.txt .

#pip-installs python packages mentioned in requirements.txt. --no-cache-dir - to avoid caching of packages and reduce image size.
#-r requirements.txt - to specify the file from which to install packages.
RUN pip install --no-cache-dir -r requirements.txt

#copy (.)first - everything from current directory.  (.) -into the Workdir of the image. (.) - means current directory of the image which is /expense_image.
COPY . .

#documents which port the app uses_#8000 - default port for Django development server.
EXPOSE 8000


#CMD - default command when the container starts
#0.0.0.0 - listen on all network interfaces
#:8000 - port inside the container.


#1️⃣ Inside a container, 127.0.0.1 means “this container itself”, not your laptop.

# 2️⃣ If Django binds to 127.0.0.1, Docker cannot forward traffic from your machine into the container.

# 3️⃣ 0.0.0.0 means “listen on all network interfaces”, so Docker can map
# localhost:8000 → container:8000.

# One-line truth to remember:

# In Docker, apps must bind to 0.0.0.0 to be reachable from outside the container.

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]