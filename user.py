import webapp2, jinja2, os, re
import hmac
import string
import random
from google.appengine.ext import db

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                              autoescape = True)

SECRET = 'yoyoyo'

def gen_salt():
    return "".join(random.choice(string.letters) for x in range(5))

def hash_str(key, string, salt):
    return str("%s|%s" % (hmac.new(key, string).hexdigest(), salt))

def verify_hash_str(key, string, hash_salt):
    hash_val, salt = hash_salt.split("|")
    gen_hash_val = hash_str(SECRET, string, salt).split("|")[0]
    return hash_val == gen_hash_val

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASSWORD_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Account(db.Model):
    email = db.EmailProperty(required=True)
    password = db.StringProperty(required=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class SignUp(Handler):
    def get(self):
        self.render("signup.html", email="", password_error="", email_error="")

    def post(self):
        #self.response.headers['Content-Type'] = 'text/plain'
        global SECRET
        
        email = self.request.get("inputEmail")
        password = self.request.get("inputPassword")
        verify = self.request.get("verifyPassword")
        password_error = ""
        email_error = ""

        if (valid_password(password) and
            valid_email(email) and
            (password == verify)):
            ascii_email = str(email)
            ascii_password = str(password)


            hash_ascii_email = hash_str(SECRET, ascii_email, gen_salt())
            hash_ascii_password = hash_str(SECRET, ascii_password, gen_salt())

            self.response.headers.add_header('Set-Cookie',
                                            'username=%s' % hash_ascii_email)
            self.response.headers.add_header('Set-Cookie',
                                              'password=%s' % hash_ascii_password)

            account = Account(email=ascii_email, password=hash_ascii_password)
            account.put()
            self.redirect("/")
        else:
            if valid_password(password):
                password_error = "That's not a valid password."
            if not (password == verify):
                password_error = "The passwords do not match up."
            if not valid_email(email):
                email_error = "The email is not valid."
            self.render("signup.html",
                        password_error=password_error,
                        email_error=email_error)


class LogIn(Handler):
    def get(self):
        self.render("login.html", password_error="", email_error="")

    def post(self):
        
        email = self.request.get("inputEmail")
        password = self.request.get("inputPassword")
        ascii_email = email.encode("ascii")

        q = Account.all().filter("email =", ascii_email)

        user = q.get()

        if user:
            hashed_password = str(user.password)
            if verify_hash_str(SECRET, password, hashed_password):
                self.response.headers.add_header('Set-Cookie',
                                                 'username=%s' % ascii_email)
                self.response.headers.add_header('Set-Cookie',
                                                 'password=%s' % hashed_password)
                self.redirect("/")
            else:
                self.render("login.html", password_error="Wrong password.")
        else:
            self.render("login.html", email_error="Sorry, can't find email in the database")



class LogOut(Handler):
    def get(self):
        self.response.delete_cookie("username")
        self.response.delete_cookie("password")
        self.redirect("/")


app = webapp2.WSGIApplication([('/signup', SignUp),
                              ('/login', LogIn),
                              ('/logout', LogOut)],
                              debug=True)










