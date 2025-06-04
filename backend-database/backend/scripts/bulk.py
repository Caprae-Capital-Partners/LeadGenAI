import requests
import json
import csv
import io
import boto3
import time
import os # Untuk mengakses variabel lingkungan

# --- Konfigurasi ---
# Ganti dengan URL endpoint API Anda
API_BASE_URL = "https://data.capraeleadseekers.site" 
API_UPLOAD_ENDPOINT = f"{API_BASE_URL}/api/upload_leads"

# Ambil API Key dari variabel lingkungan.
# API Key HARUS diatur sebagai variabel lingkungan (misalnya, export LEAD_API_KEY="...")
# Jika tidak diatur, nilai akan menjadi string kosong.
API_KEY = os.getenv("LEAD_API_KEY", "") 

# Ukuran batch untuk setiap permintaan API
# Sesuaikan ini berdasarkan kinerja API Anda dan batasan server
# Mulai dengan 500-1000, lalu bisa dioptimalkan
BATCH_SIZE = 500 

# Path file CSV lokal
CSV_FOLDER_PATH = "/Users/ghaly/Documents/Project/LeadGenAI/backend-database/split_data"

# Kolom yang wajib ada di setiap file
REQUIRED_COLUMNS = ["company", "website", "owner_linkedin"]

# Mapping kolom jika ada nama berbeda
COLUMN_MAPPING = {
    # Required fields
    "Company": "company",
    "Website": "website",
    "Owner's LinkedIn": "owner_linkedin",
    "LinkedIn URL": "owner_linkedin",
    
    # Owner Information
    "Owner First Name": "owner_first_name",
    "Owner Last Name": "owner_last_name",
    "Owner Email": "owner_email",
    "Email": "owner_email",  # Fallback
    "Owner Phone Number": "owner_phone_number",
    "Phone": "phone",
    "Owner Title": "owner_title",
    
    # Company Information
    "Company Phone": "company_phone",
    "Company LinkedIn": "company_linkedin",
    "Industry": "industry",
    "Product Category": "product_category",
    "Business Type": "business_type",
    "Employees": "employees",
    "Revenue": "revenue",
    "Year Founded": "year_founded",
    "BBB Rating": "bbb_rating",
    
    # Location Information
    "Street": "street",
    "City": "city",
    "State": "state",
    
    # Additional Information
    "Source": "source",
    "Status": "status",
    "Additional Notes": "additional_notes"
}

# --- Fungsi Pembantu ---

def send_batch_to_api(batch_data, batch_num, total_batches):
    """
    Mengirimkan satu batch data ke API upload leads.
    Menerapkan retry dengan exponential backoff untuk kegagalan sementara.
    """
    headers = {
        "Content-Type": "application/json",
        **({"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}) 
    }
    max_retries = 5
    retry_delay_seconds = 2

    for attempt in range(max_retries):
        try:
            print(f"Mengirim batch {batch_num}/{total_batches} ({len(batch_data)} data)... Percobaan {attempt + 1}/{max_retries}")
            response = requests.post(API_UPLOAD_ENDPOINT, json=batch_data, headers=headers, timeout=60) # Timeout 60 detik
            response.raise_for_status() # Akan memicu HTTPError untuk status code 4xx/5xx

            result = response.json()
            status = result.get('status', 'unknown')
            message = result.get('message', 'No message')
            
            print(f"Batch {batch_num} berhasil dikirim. Status: {status}, Pesan: {message}")
            if status == "error":
                print(f"Detail Error Batch {batch_num}: {result.get('stats', {}).get('error_details', 'N/A')}")
            return True, result

        except requests.exceptions.Timeout:
            print(f"Timeout saat mengirim batch {batch_num}. Mencoba lagi dalam {retry_delay_seconds} detik...")
            time.sleep(retry_delay_seconds)
            retry_delay_seconds *= 2 # Exponential backoff
        except requests.exceptions.ConnectionError as e:
            print(f"Kesalahan koneksi saat mengirim batch {batch_num}: {e}. Mencoba lagi dalam {retry_delay_seconds} detik...")
            time.sleep(retry_delay_seconds)
            retry_delay_seconds *= 2
        except requests.exceptions.HTTPError as e:
            print(f"Kesalahan HTTP saat mengirim batch {batch_num}: {e.response.status_code} - {e.response.text}")
            # Untuk error 4xx (misalnya 400 Bad Request), mungkin tidak perlu retry karena data salah
            # Untuk error 5xx (server error), mungkin perlu retry
            if 500 <= e.response.status_code < 600:
                print(f"Mencoba lagi dalam {retry_delay_seconds} detik...")
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2
            else:
                return False, {"status": "error", "message": f"HTTP Error {e.response.status_code}: {e.response.text}"}
        except json.JSONDecodeError:
            print(f"Gagal menguraikan respons JSON dari API untuk batch {batch_num}. Respons: {response.text}")
            return False, {"status": "error", "message": "Invalid JSON response from API"}
        except Exception as e:
            print(f"Terjadi kesalahan tak terduga saat mengirim batch {batch_num}: {e}")
            return False, {"status": "error", "message": f"Unexpected error: {str(e)}"}
    
    print(f"Gagal mengirim batch {batch_num} setelah {max_retries} percobaan.")
    return False, {"status": "error", "message": "Max retries exceeded for batch"}

def map_columns(row):
    mapped = {}
    # Mapping manual untuk kolom wajib
    mapped['company'] = row.get('Company') or row.get('Company Name') or row.get('company') or ''
    mapped['website'] = row.get('Website') or row.get('website') or ''
    mapped['owner_linkedin'] = row.get("Owner's LinkedIn") or row.get('LinkedIn URL') or row.get('owner_linkedin') or ''
    # Mapping kolom lain sesuai COLUMN_MAPPING
    for k, v in row.items():
        mapped_key = COLUMN_MAPPING.get(k.strip(), k.strip())
        if mapped_key not in mapped:  # Jangan timpa kolom wajib
            mapped[mapped_key] = v
    return mapped

# --- Skrip Utama Impor ---

def import_leads_from_folder():
    # Process all part_*.csv files
    files = [f for f in os.listdir(CSV_FOLDER_PATH)
             if f.endswith('.csv') and f.startswith('part_')]
    # Sort files to ensure they are processed in order (part_1.csv, part_2.csv, etc.)
    files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    print(f"Ditemukan {len(files)} file CSV yang dipilih di folder {CSV_FOLDER_PATH}")
    for file in files:
        file_path = os.path.join(CSV_FOLDER_PATH, file)
        print(f"\n=== Memproses file: {file} ===")
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = [h.strip() for h in reader.fieldnames]
                # Cek kolom wajib
                for col in REQUIRED_COLUMNS:
                    if col not in headers and col not in COLUMN_MAPPING.values():
                        print(f"File {file} TIDAK memiliki kolom wajib: {col}. Lewati file ini.")
                        break
                else:
                    current_batch = []
                    stats = {
                        'total_leads_processed': 0,
                        'total_added_new': 0,
                        'total_updated': 0,
                        'total_no_change': 0,
                        'total_skipped_controller': 0,
                        'total_invalid_initial_check': 0,
                        'total_errors': 0
                    }
                    all_error_details = []
                    batch_num = 1
                    for row in reader:
                        mapped_row = map_columns(row)
                        current_batch.append(mapped_row)
                        if len(current_batch) >= BATCH_SIZE:
                            success, result = send_batch_to_api(current_batch, batch_num, "N/A")
                            if success:
                                batch_stats = result.get('stats', {})
                                stats['total_added_new'] += batch_stats.get('added_new', 0)
                                stats['total_updated'] += batch_stats.get('updated', 0)
                                stats['total_no_change'] += batch_stats.get('no_change', 0)
                                stats['total_skipped_controller'] += batch_stats.get('skipped_controller', 0)
                                stats['total_invalid_initial_check'] += batch_stats.get('invalid_initial_check', 0)
                                stats['total_errors'] += batch_stats.get('errors', 0)
                                all_error_details.extend(batch_stats.get('error_details', []))
                            else:
                                stats['total_errors'] += len(current_batch)
                                all_error_details.append(f"Batch {batch_num} gagal total: {result.get('message', 'Unknown error')}")
                            stats['total_leads_processed'] += len(current_batch)
                            current_batch = []
                            batch_num += 1
                    # Sisa batch
                    if current_batch:
                        success, result = send_batch_to_api(current_batch, batch_num, "N/A")
                        if success:
                            batch_stats = result.get('stats', {})
                            stats['total_added_new'] += batch_stats.get('added_new', 0)
                            stats['total_updated'] += batch_stats.get('updated', 0)
                            stats['total_no_change'] += batch_stats.get('no_change', 0)
                            stats['total_skipped_controller'] += batch_stats.get('skipped_controller', 0)
                            stats['total_invalid_initial_check'] += batch_stats.get('invalid_initial_check', 0)
                            stats['total_errors'] += batch_stats.get('errors', 0)
                            all_error_details.extend(batch_stats.get('error_details', []))
                        else:
                            stats['total_errors'] += len(current_batch)
                            all_error_details.append(f"Batch {batch_num} gagal total: {result.get('message', 'Unknown error')}")
                        stats['total_leads_processed'] += len(current_batch)
                    print(f"\n--- Proses Impor Selesai untuk {file} ---")
                    print(f"Total data diproses: {stats['total_leads_processed']}")
                    print(f"Statistik Hasil:")
                    print(f"  - Ditambahkan Baru: {stats['total_added_new']}")
                    print(f"  - Diperbarui: {stats['total_updated']}")
                    print(f"  - Tidak Ada Perubahan: {stats['total_no_change']}")
                    print(f"  - Dilewati (Logika Controller): {stats['total_skipped_controller']}")
                    print(f"  - Tidak Valid (Pengecekan Awal): {stats['total_invalid_initial_check']}")
                    print(f"  - Error Saat Pemrosesan: {stats['total_errors']}")
                    if all_error_details:
                        print("\nDetail Error:")
                        for err in all_error_details:
                            print(f"- {err}")
        except Exception as e:
            print(f"Gagal memproses file {file}: {e}")

if __name__ == "__main__":
    import_leads_from_folder()

