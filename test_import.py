import os
import glob
from app import app, db, Invoice

def test_imports():
    files = []
    # Находим все старые эксельки (которые не начинаются с Exported_ и не Test_)
    for f in os.listdir('.'):
        if f.endswith('.xlsx') and not f.startswith('Exported_') and not f.startswith('Test_') and not f.startswith('Счет_№'):
            files.append(f)
            
    print(f"Найдено файлов для импорта: {files}")
            
    with app.app_context():
        # Сбросим базу для чистоты эксперимента:
        Invoice.query.filter_by(contract_info='Импортировано из Excel').delete()
        db.session.commit()
        
        with app.test_client() as client:
            open_files = [open(f, 'rb') for f in files]
            
            print("Отправка запросов на импорт...")
            for f in open_files:
                f.seek(0)
                data = {'excel_files': (f, os.path.basename(f.name))}
                response = client.post('/invoice/import_excel', data=data, content_type='multipart/form-data')
                with client.session_transaction() as sess:
                    flashes = sess.pop('_flashes', [])
                    print(f"Flashes after {f.name}: {flashes}")
                f.close()
            
            invoices = Invoice.query.filter_by(contract_info='Импортировано из Excel').all()
            print(f"Импортировано счетов: {len(invoices)}")
            for inv in invoices:
                items_str = ", ".join([f"{item.product.name} (x{item.quantity} по {item.price})" for item in inv.items])
                print(f"Счёт №{inv.number} от {inv.date} БИН {inv.contractor.bin_iin} ({inv.contractor.name}). Товары: {items_str}")

if __name__ == '__main__':
    test_imports()
