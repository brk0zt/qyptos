# memory/__init__.py - Eğer yoksa oluşturalım veya düzenleyelim
import logging

logger = logging.getLogger(__name__)

def check_dependencies():
    """Başlangıçta dependency'leri kontrol et"""
    dependencies = {
        'scikit-learn': 'sklearn',
        'sentence-transformers': 'sentence_transformers', 
        'transformers': 'transformers',
        'torch': 'torch',
        'opencv-python': 'cv2'
    }
    
    missing = []
    for pkg_name, import_name in dependencies.items():
        try:
            __import__(import_name)
            logger.info(f"✅ {pkg_name} yüklü")
        except ImportError:
            missing.append(pkg_name)
            logger.warning(f"❌ {pkg_name} yüklü değil")
    
    if missing:
        logger.warning(f"Eksik paketler: {', '.join(missing)}. Bazı özellikler kısıtlı çalışacak.")
    else:
        logger.info("Tüm bağımlılıklar yüklü!")

# Uygulama başladığında dependency kontrolü yap
check_dependencies()