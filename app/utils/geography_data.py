# Sample geography data for initialization
# You can expand this based on your requirements

GEOGRAPHY_DATA = {
    "continents": [
        {"name": "Asia", "code": "AS"},
        {"name": "North America", "code": "NA"},
    ],
    
    "countries": {
        "Asia": [
            {"name": "India", "code": "IN"},
        ],
        "North America": [
            {"name": "United States", "code": "US"},
            {"name": "Canada", "code": "CA"}
        ]
    },
    
    "states": {
        "India": [
            {"name": "Karnataka", "code": "KA"},
            {"name": "Maharashtra", "code": "MH"},
        ],
        "United States": [
            {"name": "California", "code": "CA"},
            {"name": "New York", "code": "NY"},
        ],
    },
    
    "cities": {
        "Karnataka": [
            {"name": "Bengaluru", "pin_code": "560001", "latitude": 12.9716, "longitude": 77.5946},
            {"name": "Mysuru", "pin_code": "570001", "latitude": 12.2958, "longitude": 76.6394},
            {"name": "Mangaluru", "pin_code": "575001", "latitude": 12.9141, "longitude": 74.8560},
            {"name": "Hubli", "pin_code": "580001", "latitude": 15.3647, "longitude": 75.1240}
        ],
        "Maharashtra": [
            {"name": "Mumbai", "pin_code": "400001", "latitude": 19.0760, "longitude": 72.8777},
            {"name": "Pune", "pin_code": "411001", "latitude": 18.5204, "longitude": 73.8567},
            {"name": "Nagpur", "pin_code": "440001", "latitude": 21.1458, "longitude": 79.0882}
        ],
    }
}