from src.app import create_app
from src.config import ProdConfig

app = create_app(ProdConfig)

if __name__ == "__main__":
    app.run()