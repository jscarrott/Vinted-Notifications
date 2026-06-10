from pyVintedVN.items.item import Item
from pyVintedVN.requester import requester
from urllib.parse import urlparse, parse_qsl
from requests.exceptions import HTTPError
from typing import List, Dict, Optional
from pyVintedVN.settings import Urls
from logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

class Items:
    """
    A class for searching and retrieving items from Vinted.

    This class provides methods to search for items on Vinted using a search URL
    and to parse Vinted search URLs into API parameters.

    Example:
        >>> items = Items()
        >>> results = items.search("https://www.vinted.fr/catalog?search_text=shoes")
    """

    def search(self, url: str, nbr_items: int = 20, page: int = 1,
               time: Optional[int] = None, json: bool = False) -> List[Item]:
        """
        Retrieve items from a given search URL on Vinted.

        Args:
            url (str): The URL of the search on Vinted.
            nbr_items (int, optional): Number of items to be returned. Defaults to 20.
            page (int, optional): Page number to be returned. Defaults to 1.
            time (int, optional): Timestamp to filter items by time. Defaults to None. Looks like it doesn't work though.
            json (bool, optional): Whether to return raw JSON data instead of Item objects. 
                Defaults to False.

        Returns:
            List[Item]: A list of Item objects.

        Raises:
            HTTPError: If the request to the Vinted API fails.
        """
        logger.info(f"Starting search with URL: {url}, items per page: {nbr_items}, page: {page}")
        
        # Extract the domain from the URL and set the locale
        locale = urlparse(url).netloc
        logger.debug(f"Extracted locale: {locale}")
        requester.set_locale(locale)

        # Parse the URL to get the API parameters
        params = self.parse_url(url, nbr_items, page, time)
        logger.debug(f"Parsed search parameters: {params}")

        # Construct the API URL
        api_url = f"https://{locale}{Urls.VINTED_API_URL}/{Urls.VINTED_PRODUCTS_ENDPOINT}"
        logger.debug(f"Constructed API URL: {api_url}")

        try:
            # Make the request to the Vinted API
            logger.info(f"Making API request to {api_url}")
            response = requester.get(url=api_url, params=params)
            response.raise_for_status()

            # Parse the response
            items = response.json()
            items = items["items"]
            logger.info(f"Successfully retrieved {len(items)} items")

            # Return either Item objects or raw JSON data
            if not json:
                item_objects = [Item(_item) for _item in items]
                logger.debug(f"Converted {len(item_objects)} items to Item objects")
                return item_objects
            else:
                logger.debug("Returning raw JSON data")
                return items

        except HTTPError as err:
            logger.error(f"HTTP error occurred during search: {str(err)}")
            raise err
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            raise

    def parse_url(self, url: str, nbr_items: int = 20, page: int = 1,
                  time: Optional[int] = None) -> Dict:
        """
        Parse a Vinted search URL to get parameters for the API call.

        Args:
            url (str): The URL of the search on Vinted.
            nbr_items (int, optional): Number of items to be returned. Defaults to 20.
            page (int, optional): Page number to be returned. Defaults to 1.
            time (int, optional): Timestamp to filter items by time. Defaults to None.

        Returns:
            Dict: A dictionary of parameters for the Vinted API.
        """
        logger.debug(f"Parsing URL: {url}")
        
        # Parse the query parameters from the URL
        queries = parse_qsl(urlparse(url).query)
        logger.debug(f"Extracted query parameters: {queries}")

        # Construct the parameters dictionary
        params = {
            "search_text": "+".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "search_text"])
            ),
            "catalog_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "catalog[]"])
            ),
            "color_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "color_ids[]"])
            ),
            "brand_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "brand_ids[]"])
            ),
            "size_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "size_ids[]"])
            ),
            "material_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "material_ids[]"])
            ),
            "status_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "status_ids[]"])
            ),
            "country_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "country_ids[]"])
            ),
            "city_ids": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "city_ids[]"])
            ),
            "is_for_swap": ",".join(
                map(str, [1 for tpl in queries if tpl[0] == "disposal[]"])
            ),
            "currency": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "currency"])
            ),
            "price_to": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "price_to"])
            ),
            "price_from": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "price_from"])
            ),
            "page": page,
            "per_page": nbr_items,
            "order": ",".join(
                map(str, [tpl[1] for tpl in queries if tpl[0] == "order"])
            ),
            "time": time
        }

        # Log non-empty parameters for debugging
        non_empty_params = {k: v for k, v in params.items() if v}
        logger.debug(f"Constructed parameters: {non_empty_params}")
        
        return params

    # Aliases for backward compatibility
    parseUrl = parse_url
