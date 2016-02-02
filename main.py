import webapp2, jinja2, os, re
from google.appengine.ext import db
from google.appengine.api import memcache, mail
import json

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

blog_memcache = memcache.Client()

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_email(email):
    return not email or EMAIL_RE.match(email)

def get_post(post_id):
    global blog_memcache
    blog_data = blog_memcache.get("ALL")
    if blog_data.get(post_id):
        return blog_data.get(post_id)
    else: 
        return Blog.get_by_id(post_id)

def add_post(post):
    global blog_memcache
    post.put()
    blog_memcache.get("ALL").update({post.key().id(): {
                                               "title": post.title,
                                               "content": post.content,
                                               "created": post.created
                                               }})

def get_posts(update = False):
    global blog_memcache
    blog_dict = {}
    
    if not update or not blog_memcache.get("ALL"):
        return self.get("ALL").values()
    else:
        self.delete("ALL")
        blog = db.all().order('-created')
        
        for post in blog:
            blog_dict[post.key().id()] = {
                                          "title": post.title,
                                          "content": post.content,
                                          "created": post.created
                                          }
        blog_memcache.set("ALL", blog_dict)
        
        blog_data = []
        for post_data in blog_dict:
            blog_data.append(post_data.values())
        return blog_data
            
def get_recent_posts(n):
    global blog_memcache
    recent_posts = blog_memcache.get("RECENT")
    if recent_posts:
        return recent_posts.items()
    else:
        recent_posts = Blog.all().order('-created').fetch(limit=n)
        blog_memcache.set("RECENT", recent_posts, time=600)
        return recent_posts
        
class Blog(db.Model):
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
    def get(self):
        recent_posts = get_recent_posts(5)
        self.render("main_page.html", blog=recent_posts)
    
class NewPage(Handler):
    def get(self):
        self.render("new_page.html")
        
    def post(self):
        title = self.request.get("title")
        content = self.request.get("content")
        post = Blog(title = title, content = content)
        add_post(post)
        self.redirect("/" + str(post.key().id()))

class IndividualPage(Handler):
    def get(self, post_id):
        post = get_post(post_id)
        self.render("permalink.html", post=post)

class AboutPage(Handler):
    def get(self):
        self.render("about.html")

class ContactPage(Handler):
    def get(self):
        self.render("contact.html")
    
    def post(self):
        name = self.request.get("inputName")
        email = self.request.get("inputEmail")
        message = self.request.get("inputMessage")
        
        if name and valid_email(email) and message:
            email_message = mail.EmailMessage(sender="%s <%s>" % (name, email),
                                              to="%s <%s>" % ("Jin Pyo Jeon", "aba1731@gmail.com"),
                                              subject="Message from Jeonjinpyo.com",
                                              body=message)
            email_message.send()
            self.render("contact.html", success="success")
        else:
            self.render("contact.html", success="failure")
        

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/about', AboutPage),
                               ('/contact', ContactPage),
                               ('/(+d)', IndividualPage)], debug = True)