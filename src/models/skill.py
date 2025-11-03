from extensions import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}

class SkillSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Skill
        load_instance = True

class FreelancerSkill(db.Model):
    __tablename__ = 'freelancer_skills'

    freelancer_profile_id = db.Column(db.Integer, db.ForeignKey('freelancer_profiles.id'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), primary_key=True)

    def to_dict(self):
        return {'freelancer_profile_id': self.freelancer_profile_id, 'skill_id': self.skill_id}

class FreelancerSkillSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FreelancerSkill
        load_instance = True