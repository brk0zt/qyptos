# memory/services/homonyms_data.py

AMBIGUOUS_TERMS = {
    'sandık': {
        'question': 'Sandık kelimesi farklı anlamlara gelebilir. Hangisini arıyorsunuz?',
        'options': [
            {'label': '📦 Hazine/Çeyiz Sandığı', 'search_query': 'wooden treasure chest object closed box'},
            {'label': '🗳️ Seçim Sandığı', 'search_query': 'ballot box voting election'},
            {'label': '👤 İnsan Göğsü (Anatomi)', 'search_query': 'human chest body part torso'}
        ]
    },
    'kare': {
        'question': 'Kare derken hangisini kastettiniz?',
        'options': [
            {'label': '🟦 Geometrik Şekil', 'search_query': 'square geometric shape'},
            {'label': '🏙️ Meydan/Alan', 'search_query': 'city square plaza'},
            {'label': '🖼️ Fotoğraf Karesi/Çerçeve', 'search_query': 'photo frame picture border'}
        ]
    },
    'yüz': {
        'question': 'Yüz kelimesi çok anlamlı:',
        'options': [
            {'label': '😊 İnsan Yüzü', 'search_query': 'human face close up portrait'},
            {'label': '💯 Sayı (100)', 'search_query': 'number 100 hundred graphic'},
            {'label': '🏊 Yüzme Eylemi', 'search_query': 'swimming person in water'}
        ]
    },
    'çay': {
        'question': 'İçecek mi yoksa doğa mı?',
        'options': [
            {'label': '☕ İçecek Olan Çay', 'search_query': 'glass of turkish tea drink beverage'},
            {'label': '🌊 Akarsu/Dere', 'search_query': 'river stream creek nature water'}
        ]
    },
    'ocak': {
        'question': 'Hangi ocak?',
        'options': [
            {'label': '🔥 Fırın/Gazlı Ocak', 'search_query': 'kitchen stove cooker appliance gas'},
            {'label': '📅 Ocak Ayı (Takvim)', 'search_query': 'january calendar winter concept'},
            {'label': '⛏️ Maden Ocağı', 'search_query': 'mining mine quarry excavation'}
        ]
    },
    'yaz': {
        'question': 'Mevsim mi eylem mi?',
        'options': [
            {'label': '☀️ Yaz Mevsimi/Güneş', 'search_query': 'summer season beach sun holiday'},
            {'label': '✍️ Yazı Yazmak', 'search_query': 'writing hand pen paper text'}
        ]
    },
    'kaz': {
        'question': 'Hayvan mı eylem mi?',
        'options': [
            {'label': '🦆 Kaz (Hayvan)', 'search_query': 'goose bird animal white goose'},
            {'label': '⛏️ Kazma Eylemi', 'search_query': 'digging soil shovel excavation'}
        ]
    },
    'at': {
        'question': 'Canlı mı eylem mi?',
        'options': [
            {'label': '🐎 At (Hayvan)', 'search_query': 'horse animal running horse'},
            {'label': '⚾ Atmak/Fırlatmak', 'search_query': 'throwing ball action throwing object'}
        ]
    },
    'dil': {
        'question': 'Organ mı lisan mı?',
        'options': [
            {'label': '👅 Dil (Organ)', 'search_query': 'human tongue mouth close up'},
            {'label': '🗣️ Konuşma/Lisan', 'search_query': 'language speech bubbles conversation text'}
        ]
    },
    'ekmek': {
        'question': 'Yiyecek mi eylem mi?',
        'options': [
            {'label': '🍞 Ekmek (Gıda)', 'search_query': 'loaf of bread bakery food'},
            {'label': '🌱 Ekmek/Dikmek (Bitki)', 'search_query': 'planting seeds gardening sowing'}
        ]
    },
    'dolu': {
        'question': 'Hava durumu mu doluluk mu?',
        'options': [
            {'label': '🌨️ Dolu Yağışı', 'search_query': 'hail storm ice rain weather'},
            {'label': '🥛 Dolu Bardak/Kap', 'search_query': 'full glass full container filled'}
        ]
    },
    'ben': {
        'question': 'Kişi mi leke mi?',
        'options': [
            {'label': '👤 Ben (Kendim/İnsan)', 'search_query': 'person pointing at self me selfie'},
            {'label': '⚫ Ben/Leke (Cilt)', 'search_query': 'mole on skin beauty mark spot'}
        ]
    },
    'bağ': {
        'question': 'Tarım mı bağlantı mı?',
        'options': [
            {'label': '🍇 Üzüm Bağı', 'search_query': 'vineyard grapes farm nature'},
            {'label': '🔗 Düğüm/Bağlantı', 'search_query': 'knot rope tie connection link'},
            {'label': '👟 Ayakkabı Bağı', 'search_query': 'shoelaces shoe tie'}
        ]
    },
    'kara': {
        'question': 'Renk mi toprak mı?',
        'options': [
            {'label': '⬛ Siyah Renk', 'search_query': 'black color dark background'},
            {'label': '🏝️ Kara Parçası/Toprak', 'search_query': 'land island ground earth'}
        ]
    },
    'yat': {
        'question': 'Araç mı eylem mi?',
        'options': [
            {'label': '🛥️ Yat/Tekne', 'search_query': 'luxury yacht boat sea vehicle'},
            {'label': '🛌 Yatmak/Uyumak', 'search_query': 'sleeping person laying down bed'}
        ]
    },
    'koy': {
        'question': 'Coğrafya mı eylem mi?',
        'options': [
            {'label': '🌊 Deniz Koyu', 'search_query': 'bay cove sea beach aerial view'},
            {'label': '📥 Koymak/Yerleştirmek', 'search_query': 'putting object placing box hand action'}
        ]
    },
    'saç': {
        'question': 'Vücut parçası mı eylem mi?',
        'options': [
            {'label': '👩 Saç (Kıl)', 'search_query': 'human hair hairstyle long hair'},
            {'label': '✨ Saçmak/Dağıtmak', 'search_query': 'scattering throwing confetti spreading'}
        ]
    },
    'al': {
        'question': 'Renk mi eylem mi?',
        'options': [
            {'label': '🔴 Al/Kırmızı', 'search_query': 'red color background red object'},
            {'label': '🤲 Almak/Tutmak', 'search_query': 'taking receiving hand holding object'}
        ]
    },
    'kır': {
        'question': 'Doğa mı eylem mi?',
        'options': [
            {'label': '🌼 Kır/Çayır', 'search_query': 'meadow field nature flowers grass'},
            {'label': '🔨 Kırmak', 'search_query': 'breaking glass smashing object broken'}
        ]
    },
    'diz': {
        'question': 'Anatomi mi eylem mi?',
        'options': [
            {'label': '🦵 Diz (Organ)', 'search_query': 'human knee leg joint anatomy'},
            {'label': '🧱 Dizmek/Sıralamak', 'search_query': 'arranging objects in row lining up'}
        ]
    },
    'yaş': {
        'question': 'Islaklık mı ömür mü?',
        'options': [
            {'label': '💧 Islak/Nemli', 'search_query': 'wet surface water drops soaked'},
            {'label': '🎂 Yaş/Doğum Günü', 'search_query': 'birthday cake age numbers candle'}
        ]
    }
}
