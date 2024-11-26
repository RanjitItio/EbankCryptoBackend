from decouple import config

# Check if the 'DB_URI' environment variable is set
def test_main():#-
    # Test case 1: When the environment variable 'DB_URI' is not set
    config('DATABASE_URL', None)
    assert main() == "No database URI found in environment variables"

    # Test case 2: When the database URI is invalid and the environment variable
    # 'DB_URI' is set
    config['DATABASE_URL'] = "invalid_db_uri"
    assert main() == "Failed to connect to the database"

    # Test case 3: When the database URI is valid and the environment variable
    # 'DB_URI' is set
    config['DATABASE_URL'] = "postgresql://username:password@localhost/dbname"
    assert main() == "Successfully connected to the database"

# Running the test cases

test_main()
