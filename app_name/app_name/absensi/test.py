import joblib
try :
    joblib.load('Scaler_Ant0.sav')
    print("berhasil")
except:
    print("Gagal")