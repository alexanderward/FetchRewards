# FetchRewards

## Running the application choose one of the following:
### Docker
- `docker-compose up`
### Local Install
- Make sure you have Python 3.x (https://www.python.org/downloads/)
- `pip install -r requirements.txt`
- `python manage.py runserver`

## API
- Domain: http://localhost:8000

| Route          | Method | Request Data Format                                                    | Response Format                                                        | Description                            |
|----------------|--------|------------------------------------------------------------------------|------------------------------------------------------------------------|----------------------------------------|
| /points/       | GET    |                                                                        | { "payer": \<string>, "points": \<integer> }[]                         | Returns user balances                  |
| /points/       | POST   | { "payer": \<string>, "points": \<integer>, "timestamp": \<datetime> } | { "payer": \<string>, "points": \<integer>, "timestamp": \<datetime> } | Creates new transaction                |
| /points/spend/ | POST   | { "points": \<integer> }                                               | { "payer": \<string>, "points": \<integer> }[]                         | Spends points and returns points spent |

## Testing
### Docker
- `docker-compose up` - if it's not already up
- `docker exec -it fetchrewards_backend_1 python manage.py test`
### Local Install
- `python manage.py test`