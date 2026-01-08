from common.repositories.factory import RepositoryFactory, RepoType
from common.models.person import Person
from common.helpers.exceptions import InputValidationError


class PersonService:

    def __init__(self, config):
        self.config = config

        from common.services import EmailService
        self.email_service = EmailService(config)

        self.repository_factory = RepositoryFactory(config)
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON)

    def save_person(self, person: Person):
        person = self.person_repo.save(person)
        return person

    def get_person_by_email_address(self, email_address: str):
        email_obj = self.email_service.get_email_by_email_address(email_address)
        if not email_obj:
            return

        person = self.person_repo.get_one({"entity_id": email_obj.person_id})
        return person

    def get_person_by_id(self, entity_id: str):
        person = self.person_repo.get_one({"entity_id": entity_id})
        return person

    def update_person_name(self, person_id: str, first_name: str, last_name: str):
        """
        Update a person's name

        Args:
            person_id: The person's entity_id
            first_name: New first name
            last_name: New last name

        Returns:
            Updated Person object

        Raises:
            InputValidationError: If first_name or last_name are empty
        """
        # Validate inputs
        if not first_name or not first_name.strip():
            raise InputValidationError("First name is required and cannot be empty.")
        if not last_name or not last_name.strip():
            raise InputValidationError("Last name is required and cannot be empty.")

        # Get the person
        person = self.get_person_by_id(person_id)
        if not person:
            raise InputValidationError("Person not found.")

        # Update name fields
        person.first_name = first_name.strip()
        person.last_name = last_name.strip()

        # Save and return
        person = self.save_person(person)
        return person