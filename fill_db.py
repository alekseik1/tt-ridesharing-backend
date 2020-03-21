from app import create_app, db
from main_app.fixtures.organizations import OrganizationFactory

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        organization = OrganizationFactory()
        db.session.add(organization)
        db.session.commit()
