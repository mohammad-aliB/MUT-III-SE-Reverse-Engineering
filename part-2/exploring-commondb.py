import os
import xml.etree.ElementTree as ET
from pprint import pprint

def find_vin_search_file(vin: str, commonDB_path: str) -> str:
    """
    Identifies the correct VIN_Search_XXX.xml file for the given VIN using VIN_Selection.xml
    Args:
        vin: The VIN to search for
        commonDB_path: The path to the CommonDB directory
    Returns:
        The path to the VIN_Search_XXX.xml file
    """

    selection_file = os.path.join(commonDB_path, "VIN_Selection.xml")

    for file_elem in ET.parse(selection_file).find("ALL").findall("FILE"):
        vin_from = file_elem.find("VIN_FROM").text
        vin_to = file_elem.find("VIN_TO").text
        if vin_from <= vin <= vin_to:
            # swap extension from .exdf to .xml
            return file_elem.find("NAME").text.replace(".exdf", ".xml")

def lookup_vin(vin: str, search_file_name: str, commonDB_path: str) -> dict:
    """
    Looks up the VIN in the appropriate VIN_Search_XXX.xml file
    Args:
        vin: The VIN to search for
        search_file_name: The name of the VIN_Search_XXX.xml file
        commonDB_path: The path to the CommonDB directory
    Returns:
        A dictionary containing the VIN information
    """
    search_file = os.path.join(commonDB_path, search_file_name)

    for vi_elem in ET.parse(search_file).findall("VI"):
        if vi_elem.get("VN") == vin:
            return {
                "VehicleYear": vi_elem.find("MY").text,
                "VehicleType": vi_elem.find("TY").text,
                "VehicleKind": vi_elem.find("KD").text,
            }

def vehicle_config(destination: str, vin_info: dict, commonDB_path: str) -> dict:
    """
    Looks up the vehicle information from the Vehicle_DB.xml file
    Args:
        destination: The destination ID
        vin_info: Dictionary containing VehicleType, VehicleKind, VehicleYear
        commonDB_path: The path to the CommonDB directory
    Returns:
        A dictionary containing the vehicle information.
    """
    vehicle_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(vehicle_db_file)
    for vehicles_for_destination in tree.find("CONFIG").findall("ID"):
        if vehicles_for_destination.get("DSTN_ID") == destination:
            for vehicle in vehicles_for_destination.findall("VHCL"):
                if (
                    vehicle.get("TYPE") == vin_info["VehicleType"]
                    and vehicle.get("KIND") == vin_info["VehicleKind"]
                    and vehicle.get("MODEL_YR") == vin_info["VehicleYear"]
                ):
                    return {
                        "VHCL_ID": vehicle.find("VHCL_ID").text,
                        "ENGINE_ID": vehicle.find("ENGINE_ID").text,
                        "TRANSMISSION_ID": vehicle.find("TRANSMISSION_ID").text,
                        "VHCL_VIEW": vehicle.find("VHCL_VIEW").text,
                        "MAKER_ID": vehicle.find("MAKER_ID").text,
                        "DCSMV": vehicle.find("DCSMV").text,
                        "VEHICLE_FAMILY": vehicle.find("VEHICLE_FAMILY").text,
                    }


def canbus_spec(destination: str, vin_info: dict, commonDB_path: str) -> dict:
    """
    Looks up CAN bus specification using destination-aware search
    Args:
        destination: The destination ID (e.g., "002" for NAFTA).
        vin_info: Dictionary with VehicleType, VehicleKind, VehicleYear.
        commonDB_path: Path to the CommonDB directory.
    Algorithm:
        1. Find all CANBUS_SPEC entries matching Type/Kind/ModelYear
        2. If only 1 match exists, return it (regardless of DSTN_ID)
        3. If multiple matches exist, return the one matching the destination argument
    Returns:
        Dictionary with CANBUS_ID and PASSTHRU, or None if not found.
    """
    vehicle_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(vehicle_db_file)
    
    # Collect all matching entries from all DSTN_ID sections
    matches = []
    for id_elem in tree.find("CANBUS_SPEC").findall("ID"):
        dstn_id = id_elem.get("DSTN_ID")
        for vhcl in id_elem.findall("VHCL"):
            if (
                vhcl.get("TYPE") == vin_info["VehicleType"]
                and vhcl.get("KIND") == vin_info["VehicleKind"]
                and vhcl.get("MODEL_YR") == vin_info["VehicleYear"]
            ):
                matches.append({
                    "DSTN_ID": dstn_id,
                    "CANBUS_ID": vhcl.find("CANBUS_ID").text,
                    "PASSTHRU": vhcl.find("PASSTHRU").text,
                })
    
    # If only 1 match, return it
    if len(matches) == 1:
        return {"CANBUS_ID": matches[0]["CANBUS_ID"], "PASSTHRU": matches[0]["PASSTHRU"]}   
    # If multiple matches, find the one for the given destination
    elif len(matches) > 1:
        for match in matches:
            if match["DSTN_ID"] == destination:
                return {"CANBUS_ID": match["CANBUS_ID"], "PASSTHRU": match["PASSTHRU"]}

def engine_name(engine_id: str, commonDB_path: str) -> str:
    """
    Looks up the engine name from the ENGINE_DB.xml file.
    Args:
        engine_id: The ID of the engine.
        commonDB_path: The path to the CommonDB directory.
    Returns:
        The name of the engine.
    """
    engine_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(engine_db_file)
    for engine in tree.find("CONFIG_ENGINE").findall("ID"):
        if engine.get("ENGINE_ID") == engine_id:
            return engine.find("ENGINE_NM").text
    print(f"Error: Engine not found in {engine_db_file}")


def transmission_name(transmission_id: str, commonDB_path: str) -> str:
    """
    Looks up the transmission name from the TRANSMISSION_DB.xml file.
    Args:
        transmission_id: The ID of the transmission.
        commonDB_path: The path to the CommonDB directory.
    Returns:
        The name of the transmission.
    """
    transmission_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(transmission_db_file)
    for transmission in tree.find("CONFIG_TRANSMISSION").findall("ID"):
        if transmission.get("TRANSMISSION_ID") == transmission_id:
            return transmission.find("TRANSMISSION_NM").text
    print(f"Error: Transmission not found in {transmission_db_file}")


def model_name(model_id: str, destination: str, commonDB_path: str) -> str:
    """
    Looks up the model name from the MODEL_DB.xml file.
    Args:
        model_id: The ID of the model.
        destination: The destination of the vehicle.
        commonDB_path: The path to the CommonDB directory.
    Returns:
        The name of the model.
    """
    model_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(model_db_file)
    for model in tree.find("MST_VHCL").findall("ID"):
        if model.get("DSTN_ID") == destination:
            for model in model.findall("VHCL"):
                if model.get("VHCL_ID") == model_id:
                    return model.find("VHCL_NM").text
    print(f"Error: Model name not found in {model_db_file}")


def destination_name(destination: str, commonDB_path: str) -> str:
    """
    Looks up the destination name from the Vehicle_DB.xml file.
    Args:
        destination: The destination of the vehicle.
        commonDB_path: The path to the CommonDB directory.
    Returns:
        The name of the destination.
    """
    dest_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(dest_db_file)
    for dest in tree.find("MST_DSTN").findall("ID"):
        if dest.get("DSTN_ID") == destination:
            return dest.find("DSTN_NM").text
    print(f"Error: Destination name not found in {dest_db_file}")


def maker_name(maker_id: str, commonDB_path: str) -> str:
    """
    Looks up the maker name from the MAKER_DB.xml file.
    Args:
        maker_id: The ID of the maker.
        commonDB_path: The path to the CommonDB directory.
    Returns:
        The name of the maker.
    """
    maker_db_file = os.path.join(commonDB_path, "Vehicle_DB.xml")
    tree = ET.parse(maker_db_file)
    for maker in tree.find("MST_MAKER").findall("ID"):
        if maker.get("MAKER_ID") == maker_id:
            return maker.find("MAKER_NM").text
    print(f"Error: Maker name not found in {maker_db_file}")


if __name__ == "__main__":
    vin = "ML32A3HJ1FH050391"
    commonDB_path = "MUT3_SE/CommonDB"
    # Retrieved from Vehicle_DB.xml MST_DSTN element
    # - 001 is Japan
    # - 002 is North America
    # - 003 is Europe
    # - 004 is Export
    # - 008 is Australia
    destination = "002"
    search_file_name = find_vin_search_file(vin, commonDB_path)
    vin_info = lookup_vin(vin, search_file_name, commonDB_path)
    vehicle_config = vehicle_config(destination, vin_info, commonDB_path)
    canbus_spec = canbus_spec(destination, vin_info, commonDB_path)
    engine_name = engine_name(vehicle_config["ENGINE_ID"], commonDB_path)
    transmission_name = transmission_name(vehicle_config["TRANSMISSION_ID"], commonDB_path)
    model_name = model_name(vehicle_config["VHCL_ID"], destination, commonDB_path)
    destination_name = destination_name(destination, commonDB_path)
    maker_name = maker_name(vehicle_config["MAKER_ID"], commonDB_path)
    print("VIN information:")
    pprint(vin_info)
    print("vehicle configuration:")
    pprint(vehicle_config)
    print("canbus specification:")
    pprint(canbus_spec)
    print(f"engine name: {engine_name}")
    print(f"transmission name: {transmission_name}")
    print(f"model name: {model_name}")
    print(f"destination name: {destination_name}")
    print(f"maker name: {maker_name}")
