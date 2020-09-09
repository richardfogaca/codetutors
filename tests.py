from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import Users, Tutors, Reviews, Categories

class UserModelCase(unittest.TestCase):
    # unit testing executes setUp before each test
    # configuring to use SQLite, so the testing unit doesn't use the standard DB
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()
    
    # unit testing executes tearDown after each test
    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = Users(first_name='Steve', last_name='Job', email='steve@test.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))
    
    def test_follow(self):
        u1 = Users(first_name='john', last_name="wonders", email='john@example.com')
        u2 = Users(first_name='susan', last_name="Collins", email='susan@example.com')
        u1.set_password('cat')
        u2.set_password('dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        
        t1 = Tutors(user_id=u2.id, price=50)
        u1.follow(t1)
        db.session.commit()
        self.assertTrue(u1.is_following(t1))
        self.assertEqual(u1.following_total(), 1)
        self.assertEqual(u1.followed.first().price, 50)
        self.assertEqual(t1.followers_total(), 1)
        self.assertEqual(t1.followers.first().first_name, 'john')

if __name__ == '__main__':
    unittest.main(verbosity=2)
