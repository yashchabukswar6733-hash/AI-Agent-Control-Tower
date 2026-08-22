from datetime import datetime
import uuid


class ClientManager:

    def __init__(self):
        self.clients = {}

    def create_client(self, name, company):
        client_id = uuid.uuid4().hex[:8]

        client = {
            "id": client_id,
            "name": name,
            "company": company,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }

        self.clients[client_id] = client

        return client

    def list_clients(self):
        return list(self.clients.values())

    def get_client(self, client_id):
        return self.clients.get(client_id)

    def delete_client(self, client_id):
        if client_id not in self.clients:
            return False

        del self.clients[client_id]
        return True


client_manager = ClientManager()