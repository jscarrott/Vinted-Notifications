import db, configuration_values, requests
from pyVintedVN import Vinted, requester
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

def process_query(query):
    """
    Process a Vinted query URL by:
    1. Parsing the URL and extracting query parameters
    2. Ensuring the order flag is set to "newest_first"
    3. Removing time and search_id parameters
    4. Rebuilding the query string and URL
    5. Checking if the query already exists in the database
    6. Adding the query to the database if it doesn't exist

    Args:
        query (str): The Vinted query URL

    Returns:
        tuple: (message, is_new_query)
            - message (str): Status message
            - is_new_query (bool): True if query was added, False if it already existed
    """
    logger.debug(f"Processing query: {query}")
    
    try:
        # Parse the URL and extract the query parameters
        parsed_url = urlparse(query)
        query_params = parse_qs(parsed_url.query)
        logger.debug(f"Extracted query parameters: {query_params}")

        # Ensure the order flag is set to newest_first
        query_params['order'] = ['newest_first']
        # Remove time and search_id if provided
        query_params.pop('time', None)
        query_params.pop('search_id', None)
        query_params.pop('disabled_personalization', None)
        query_params.pop('page', None)
        logger.debug("Cleaned query parameters")

        searched_text = query_params.get('search_text')
        if searched_text:
            logger.debug(f"Search text found: {searched_text[0]}")

        # Rebuild the query string and the entire URL
        new_query = urlencode(query_params, doseq=True)
        processed_query = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
        logger.debug(f"Processed query URL: {processed_query}")

        # Some queries are made with filters only, so we need to check if the search_text is present
        if db.is_query_in_db(processed_query) is True:
            logger.info(f"Query already exists in database: {processed_query}")
            return "Query already exists.", False
        else:
            # add the query to the db
            db.add_query_to_db(processed_query)
            logger.info(f"Added new query to database: {processed_query}")
            return "Query added.", True
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise

def get_formatted_query_list():
    """
    Get a formatted list of all queries in the database.

    Returns:
        str: A formatted string with all queries, numbered
    """
    logger.debug("Getting formatted query list")
    try:
        all_queries = db.get_queries()
        queries_keywords = []
        for query in all_queries:
            parsed_url = urlparse(query[1])
            query_params = parse_qs(parsed_url.query)

            # Extract the value of 'search_text'
            search_text = query_params.get('search_text', [None])

            if search_text[0] is None:
                # Use query text instead of the whole query object
                queries_keywords.append([query[1]])
            else:
                queries_keywords.append(search_text)

        query_list = ("\n").join([str(i + 1) + ". " + j[0] for i, j in enumerate(queries_keywords)])
        logger.debug(f"Formatted {len(queries_keywords)} queries")
        return query_list
    except Exception as e:
        logger.error(f"Error getting formatted query list: {str(e)}", exc_info=True)
        raise

def process_remove_query(number):
    """
    Process the removal of a query from the database.

    Args:
        number (str): The number of the query to remove or "all" to remove all queries

    Returns:
        tuple: (message, success)
            - message (str): Status message
            - success (bool): True if query was removed successfully
    """
    logger.debug(f"Processing query removal request: {number}")
    try:
        if number == "all":
            db.remove_all_queries_from_db()
            logger.info("Removed all queries from database")
            return "All queries removed.", True

        # Check if number is a valid digit
        if not number[0].isdigit():
            logger.warning(f"Invalid query number provided: {number}")
            return "Invalid number.", False

        # Remove the query from the database
        db.remove_query_from_db(number)
        logger.info(f"Removed query number {number} from database")
        return "Query removed.", True
    except Exception as e:
        logger.error(f"Error removing query: {str(e)}", exc_info=True)
        raise

def process_add_country(country):
    """
    Process the addition of a country to the allowlist.

    Args:
        country (str): The country code to add

    Returns:
        tuple: (message, country_list)
            - message (str): Status message
            - country_list (list): Current list of allowed countries
    """
    logger.debug(f"Processing country addition request: {country}")
    try:
        # Format the country code (remove spaces)
        country = country.replace(" ", "")
        country_list = db.get_allowlist()

        # Validate the country code (check if it's 2 characters long)
        if len(country) != 2:
            logger.warning(f"Invalid country code provided: {country}")
            return "Invalid country code", country_list

        # Check if the country is already in the allowlist
        # If country_list is 0, it means the allowlist is empty
        if country_list != 0 and country.upper() in country_list:
            logger.info(f"Country {country.upper()} already in allowlist")
            return f'Country "{country.upper()}" already in allowlist.', country_list

        # Add the country to the allowlist
        db.add_to_allowlist(country.upper())
        logger.info(f"Added country {country.upper()} to allowlist")
        return "Country added.", db.get_allowlist()
    except Exception as e:
        logger.error(f"Error adding country: {str(e)}", exc_info=True)
        raise

def process_remove_country(country):
    """
    Process the removal of a country from the allowlist.

    Args:
        country (str): The country code to remove

    Returns:
        tuple: (message, country_list)
            - message (str): Status message
            - country_list (list): Current list of allowed countries
    """
    logger.debug(f"Processing country removal request: {country}")
    try:
        # Format the country code (remove spaces)
        country = country.replace(" ", "")

        # Validate the country code (check if it's 2 characters long)
        if len(country) != 2:
            logger.warning(f"Invalid country code provided: {country}")
            return "Invalid country code", db.get_allowlist()

        # Remove the country from the allowlist
        db.remove_from_allowlist(country.upper())
        logger.info(f"Removed country {country.upper()} from allowlist")
        return "Country removed.", db.get_allowlist()
    except Exception as e:
        logger.error(f"Error removing country: {str(e)}", exc_info=True)
        raise

def get_user_country(profile_id):
    """
    Get the country code for a Vinted user.

    Makes an API request to retrieve the user's country code.
    Handles rate limiting by trying an alternative endpoint.

    Args:
        profile_id (str): The Vinted user's profile ID

    Returns:
        str: The user's country code (2-letter ISO code) or "XX" if it can't be determined
    """
    logger.debug(f"Getting country for user {profile_id}")
    try:
        # Users are shared between all Vinted platforms, so we can use whatever locale we want
        url = f"https://www.vinted.fr/api/v2/users/{profile_id}?localize=false"
        response = requester.get(url)
        # That's a LOT of requests, so if we get a 429 we wait a bit before retrying once
        if response.status_code == 429:
            logger.warning(f"Rate limited when getting user country for {profile_id}, trying alternative endpoint")
            # In case of rate limit, we're switching the endpoint. This one is slower, but it doesn't RL as soon. 
            # We're limiting the items per page to 1 to grab as little data as possible
            url = f"https://www.vinted.fr/api/v2/users/{profile_id}/items?page=1&per_page=1"
            response = requester.get(url)
            try:
                user_country = response.json()["items"][0]["user"]["country_iso_code"]
                logger.debug(f"Got country {user_country} for user {profile_id} from alternative endpoint")
            except KeyError:
                logger.warning(f"Couldn't get the country for user {profile_id} due to too many requests. Returning default value.")
                user_country = "XX"
        else:
            user_country = response.json()["user"]["country_iso_code"]
            logger.debug(f"Got country {user_country} for user {profile_id}")
        return user_country
    except Exception as e:
        logger.error(f"Error getting user country: {str(e)}", exc_info=True)
        return "XX"

def process_items(queue):
    """
    Process all queries from the database, search for items, and put them in the queue.
    Uses the global items_queue by default, but can accept a custom queue for backward compatibility.

    Args:
        queue (Queue, optional): The queue to put the items in. Defaults to the global items_queue.

    Returns:
        None
    """
    logger.debug("Starting to process items")
    try:
        all_queries = db.get_queries()
        logger.debug(f"Found {len(all_queries)} queries to process")

        # Initialize Vinted
        vinted = Vinted()

        # Get the number of items per query from the database
        items_per_query = int(db.get_parameter("items_per_query"))
        logger.debug(f"Using {items_per_query} items per query")

        # for each keyword we parse data
        for query in all_queries:
            logger.debug(f"Processing query: {query[1]}")
            all_items = vinted.items.search(query[1], nbr_items=items_per_query)
            # Filter to only include new items. This should reduce the amount of db calls.
            data = [item for item in all_items if item.is_new_item()]
            queue.put((data, query[0]))
            logger.info(f"Scraped {len(data)} new items for query: {query[1]}")
    except Exception as e:
        logger.error(f"Error processing items: {str(e)}", exc_info=True)
        raise

def clear_item_queue(items_queue, new_items_queue):
    """
    Process items from the items_queue.
    This function is scheduled to run frequently.
    """
    if not items_queue.empty():
        logger.debug("Processing items from queue")
        try:
            data, query_id = items_queue.get()
            logger.debug(f"Processing {len(data)} items for query ID {query_id}")
            
            for item in reversed(data):
                # If already in db, pass
                last_query_timestamp = db.get_last_timestamp(query_id)
                if last_query_timestamp is not None and last_query_timestamp >= item.raw_timestamp:
                    logger.debug(f"Item {item.id} already in database, skipping")
                    pass

                # If there's an allowlist and
                # If the user's country is not in the allowlist, we just update the timestamp
                elif db.get_allowlist() != 0 and (get_user_country(item.raw_data["user"]["id"])) not in (
                        db.get_allowlist() + ["XX"]):
                    logger.debug(f"Item {item.id} from non-allowed country, updating timestamp only")
                    db.update_last_timestamp(query_id, item.raw_timestamp)
                    pass
                else:
                    # We create the message
                    content = configuration_values.MESSAGE.format(
                        title=item.title,
                        price=str(item.price) + " " + item.currency,
                        brand=item.brand_title,
                        image=None if item.photo is None else item.photo
                    )
                    # add the item to the queue
                    new_items_queue.put((content, item.url, "Open Vinted", None, None))
                    # new_items_queue.put((content, item.url, "Open Vinted", item.buy_url, "Open buy page"))
                    # Add the item to the db
                    db.add_item_to_db(id=item.id, timestamp=item.raw_timestamp, price=item.price, title=item.title,
                                    photo_url=item.photo, query_id=query_id, currency=item.currency)
                    logger.info(f"Added new item {item.id} to queue and database")
        except Exception as e:
            logger.error(f"Error processing item queue: {str(e)}", exc_info=True)
            raise

def check_version():
    """
    Check if the application is up to date
    """
    logger.debug("Checking for new version")
    try:
        # Get URL from the database
        github_url = db.get_parameter("github_url")
        # Get version from the database
        ver = db.get_parameter("version")
        # Get latest version from the repository
        url = f"{github_url}/releases/latest"
        response = requests.get(url)

        if response.status_code == 200:
            latest_version = response.url.split('/')[-1]
            is_up_to_date = (ver == latest_version)
            logger.info(f"Version check complete. Current: {ver}, Latest: {latest_version}, Up to date: {is_up_to_date}")
            return is_up_to_date, ver, latest_version, github_url
        else:
            logger.warning(f"Failed to check version. Status code: {response.status_code}")
            # If we can't check, assume it's up to date
            return True, ver, ver, github_url
    except Exception as e:
        logger.error(f"Error checking for new version: {str(e)}", exc_info=True)
        # If we can't check, assume it's up to date
        return True, ver, ver, github_url
