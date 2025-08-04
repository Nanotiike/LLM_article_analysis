import os
import sys

import httpx
import pytest
import pytest_asyncio

# Hold the functions hand to the right folder so that imports work consistantly
project_root = os.path.abspath(os.path.join(__file__, "../.."))
sys.path.append(str(project_root))

from backend_analytics.analytics.config import settings
from backend_analytics.analytics.service.analysis_service import AnalysisService
from backend_analytics.analytics.utils.excel_writer import ExcelWriter


@pytest_asyncio.fixture(scope="function")
async def async_client():
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture(scope="function")
def service():
    service = AnalysisService(model="ark-gpt-4o")
    yield service


@pytest.fixture(scope="session")
def writer():
    if settings.EXCEL_PATH != "":
        file_path = f"{settings.EXCEL_PATH}/test_results.xlsx"
        writer = ExcelWriter(str(file_path))
        yield writer
        # after all tests
        writer.close()
        print(f"\nExcel output written to {file_path}")
    else:
        print("EXCEL_PATH not set, skipping ExcelWriter.")
        yield None


# Example mock response that matches the expected structure
@pytest.fixture
def request_data():
    return {
        "metadata": {"count_words": "72", "slug": "parempaa-tietoa"},
        "ingress": "",
        "id": "8185975",
        "title": "title",
        "kicker": "test",
        "body": "Eiran kaupunginosa Helsingissä on tunnettu kauniista jugendtyylisistä rakennuksistaan ja rauhallisesta tunnelmastaan. Tämä viehättävä alue, joka sijaitsee aivan meren äärellä, tarjoaa täydellisen pakopaikan kiireiseltä kaupunkielämältä. Eirassa sijaitsee myös eräs helsinkiläisten suosikkipaikoista: Cafe Eira. Cafe Eira on pieni ja kodikas kahvila, jonka ovet ovat avoinna niin paikallisille asukkaille kuin turistikin. Kahvilaa pyörittää sympaattinen Helena Virtanen, joka on tunnettu ystävällisestä palvelustaan ja herkullisista leivonnaisista. Helena perusti Cafe Eiran 10 vuotta sitten, ja siitä lähtien kahvila on ollut Eiran alueen sydän. Kävijät voivat nauttia kahvinsa ja tuoreensa leivonnaiset samalla ihaillen ikkunasta avautuvaa näkymää vehreään puistoon ja merelle. Helenan kädenjälki näkyy niin menuvalikoimassa kuin sisustuksessakin; kahvilan seinät ovat koristeltu paikallisten taiteilijoiden töillä, ja pöydillä on tuoreita kukkakimppuja. Eirassa sijaitsee myös Suomen Taiteilijaseura, joka tukee ja edistää suomalaisten taiteilijoiden työtä. Järjestö on perustanut useita näyttelyitä ja tapahtumia, jotka tuovat esiin uusiä ja tunnettuja tekijöitä. Yksi taiteilijaseuran suojateista, Ville Lahtinen, asuu myös Eirassa. Hänen maalausensa ovat saaneet inspiraationsa juuri tästä kauniista ympäristöstä, ja ne elävät ikään kuin Eiran tunnelman ja maisemien jatkeena. Kävelyretki merenrannalla, kahvihetki Cafe Eirassa ja vierailu Suomen Taiteilijaseuran näyttelyyn – päivä Eirassa tarjoaa unohtumattoman kokemuksen niin taiteen kuin kaupunkielämän ystäville. Tämä kaupunginosa on kuin pieni keidas suurkaupungin keskellä, jossa yhdistyvät historia, kulttuuri ja moderni elämäntyyli.",
        "url": "https://www.testi.fi/artikkeli",
        "paywall_status": "free",
        "category": "Testi",
        "domain": "TT",
        "brand": "testi sanomat",
        "content_type": "story",
        "partner": "",
        "tags": ["testi", "arviointi"],
        "authors_writers": ["DAIN"],
        "authors_photographers": ["DAIN"],
        "publish_date": "2025-01-03T12:06:50.000Z",
        "update_date": "2025-01-03T12:06:50.000Z",
    }


@pytest.fixture
def mock_analyse_all_response():
    return {
        "people": ["Person 1", "Person 2"],
        "locations": ["Location 1", "Location 2"],
        "organisations": ["Organisation 1", "Organisation 2"],
        "summary": ["Summary point 1", "Summary point 2", "Summary point 3"],
        "hyperlocation": {
            "country": "Finland",
            "city": "Helsinki",
            "neighborhood": "Kallio",
        },
        "user_need": {
            "analysis": "Sample analysis",
            "drive": "Sample drive",
            "scoring": {"Tiedä": 30, "Ymmärrä": 30, "Tunne": 40, "Toimi": 0},
            "detailed_scoring": {
                "tiedä": {
                    "Kerro mitä tapahtui": 20,
                    "Pidä minut ajan tasalla keskustelussa": 10,
                },
                "Toimi": {"Anna neuvoja": 0, "Luo yhteyksiä muihin": 0},
                "Tunne": {"Virkistä": 10, "Inspiroi": 30},
                "Ymmärrä": {
                    "Aseta mittasuhteisiin, anna näkökulmaa": 15,
                    "Sivistä": 15,
                },
            },
        },
        "tone": {
            "yleissävy": {
                "analysis": "Sample tone analysis",
                "tone": "positive",
            }
        },
        "theme_and_topics": {
            "theme": "Sample theme",
            "topics": ["Topic 1", "Topic 2"],
        },
    }
