from database import Database

def main():

    db = Database()

    db.query(db.drop_table)
    db.create_db_table(db.DATABASE_NAME, db.TABLE_NAME, db.convert_csv_to_df())

    result = db.query(db.commute_data)
    # result = db.query(db.morning_commute)
    # result = db.query(db.afternoon_commute)
    db.print_commute_specific_query_results(result)


if __name__ == '__main__':
    main()
