import os
from pathlib import Path

import brightway2 as bw
import pytest
import wurst

from premise import DATA_DIR, NewDatabase
from premise.cars import Cars

REGION_MAPPING_FILEPATH = DATA_DIR / "regionmappingH12.csv"

# for local test runs
remind_output_folder = Path(__file__).resolve().parent / "data"
BW_PROJECT = "transport_lca_Budg1100_Conv"
scenario = "SSP2-PkBudg1100"
year = 2035
remind_regions = ["LAM", "EUR"]
ecoinvent_version = 3.7


def get_db():
    db = [
        {
            "name": "fake activity",
            "reference product": "fake product",
            "location": "IAI Area, Africa",
            "unit": "kilogram",
            "exchanges": [
                {
                    "name": "fake activity",
                    "product": "fake product",
                    "amount": 1,
                    "type": "production",
                    "unit": "kilogram",
                    "input": ("dummy_db", "6543541"),
                },
                {
                    "name": "1,4-Butanediol",
                    "categories": ("air", "urban air close to ground"),
                    "amount": 1,
                    "type": "biosphere",
                    "unit": "kilogram",
                    "input": ("dummy_bio", "123"),
                },
            ],
        },
        {
            "name": "electricity supply for electric vehicles",
            "reference product": "electricity, low voltage",
            "location": "RER",
            "unit": "kilowatt hour",
            "exchanges": [
                {
                    "name": "electricity supply for electric vehicles",
                    "product": "fake product",
                    "amount": 1,
                    "type": "production",
                    "unit": "kilogram",
                    "input": ("dummy_db", "6543541"),
                },
                {
                    "name": "1,4-Butanediol",
                    "categories": ("air", "urban air close to ground"),
                    "amount": 1,
                    "type": "biosphere",
                    "unit": "kilogram",
                    "input": ("dummy_bio", "123"),
                },
            ],
        },
        {
            "name": "BEV,",
            "reference product": "car",
            "location": "RER",
            "unit": "car",
            "exchanges": [
                {
                    "name": "BEV,",
                    "product": "fake product",
                    "amount": 1,
                    "type": "production",
                    "unit": "kilogram",
                    "input": ("dummy_db", "6543541"),
                },
                {
                    "name": "electricity supply for electric vehicles",
                    "product": "fake product",
                    "amount": 1,
                    "type": "technosphere",
                    "unit": "kilogram",
                    "input": ("dummy_db", "6543541"),
                },
            ],
        },
        *[
            {
                "name": "market group for electricity, low voltage",
                "reference product": "electricity, low voltage",
                "location": region,
                "unit": "kilowatt hour",
            }
            for region in remind_regions
        ],
    ]
    version = ecoinvent_version
    return db, version


def setup_db():
    bw.projects.set_current(BW_PROJECT)
    return NewDatabase(
        scenarios=[
            {
                "model": "remind",
                "pathway": scenario,
                "year": year,
                "exclude": ["update_electricity", "update_steel", "update_cement"],
                "passenger_cars": {"regions": ["EUR"]},
            }
        ],
        source_db="ecoinvent 3.7 cutoff",
        source_version="3.7",
        key=os.environ["IAM_FILES_KEY"],
    )


def setup_db_with_custom_fleet_file():
    bw.projects.set_current(BW_PROJECT)
    return NewDatabase(
        scenarios=[
            {
                "model": "remind",
                "pathway": scenario,
                "year": year,
                "exclude": ["update_electricity", "update_steel", "update_cement"],
                "passenger_cars": {
                    "regions": ["EUR"],
                    "fleet file": remind_output_folder
                    / "fleet_files"
                    / "remind"
                    / "passenger_cars"
                    / "fleet_file.csv",
                },
            }
        ],
        source_db="ecoinvent 3.7 cutoff",
        source_version="3.7",
    )


@pytest.mark.ecoinvent
def test_link_local_electricity_supply():
    ndb = setup_db()

    ndb.update_electricity()
    Cars(ndb.db, ndb.rdc, scenario, year, ndb.model).link_local_electricity_supply()


@pytest.mark.ecoinvent
def test_link_local_liquid_fuel_markets():
    bw.projects.set_current(BW_PROJECT)

    ndb = setup_db()

    ndb.update_electricity()
    Cars(ndb.db, ndb.rdc, scenario, year, ndb.model).link_local_liquid_fuel_markets()


@pytest.mark.ecoinvent
def test_full_import():
    bw.projects.set_current(BW_PROJECT)

    ndb = setup_db()

    ndb.update_electricity()
    ndb.update_cars()
    dbname = "test_carculator_complete"
    if dbname in bw.databases:
        del bw.databases[dbname]
    wurst.write_brightway2_database(ndb.db, dbname)
    del bw.databases[dbname]
