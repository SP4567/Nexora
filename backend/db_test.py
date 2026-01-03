from db import Database
import traceback

try:
    db = Database()
    print('engine ok')
    ok = db.test_connection()
    print('test_connection:', ok)
    try:
        df = db.fetch_dataframe('SELECT date, revenue FROM sales LIMIT 3')
        print('rows', len(df))
        print(df.to_dict(orient='records'))
    except Exception:
        print('fetch error')
        traceback.print_exc()
except Exception:
    print('init error')
    traceback.print_exc()
