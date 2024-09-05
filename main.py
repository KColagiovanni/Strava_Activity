from database import Database

def main():

    db = Database

    print(db.test_query)
    db.query(db.test_query)


if __name__ == '__main__':
    main()
