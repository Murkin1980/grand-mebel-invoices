import os
from app import app

def test():
    with app.app_context():
        with app.test_client() as client:
            # Let's test waybill export for invoice 1
            print("Requesting waybill for Invoice 1...")
            response = client.get('/invoice/export_waybill/1')
            print("Status:", response.status_code)
            if response.status_code == 200:
                with open('test_waybill_out.xlsx', 'wb') as f:
                    f.write(response.data)
                print("Generated test_waybill_out.xlsx")
            else:
                print("Error, see response headers or start server to see traceback")

if __name__ == '__main__':
    test()
