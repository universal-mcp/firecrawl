from typing import Any, Optional, Type

from loguru import logger

try:
    from firecrawl import FirecrawlApp
    FirecrawlApiClient: Type[FirecrawlApp] | None = FirecrawlApp
except ImportError:
    FirecrawlApiClient = None
    logger.error("Failed to import FirecrawlApp. Please ensure 'firecrawl-py' is installed.")


from universal_mcp.applications import APIApplication
from universal_mcp.integrations import Integration
from universal_mcp.exceptions import NotAuthorizedError, ToolError


class FirecrawlApp(APIApplication):
    """
    Application for interacting with the Firecrawl service (firecrawl.dev)
    to scrape web pages, perform searches, and manage crawl/batch scrape/extract jobs.
    Requires a Firecrawl API key configured via integration.
    Authentication is handled by the configured Integration, fetching the API key.
    """

    def __init__(self, integration: Integration | None = None, **kwargs: Any) -> None:
        super().__init__(name="firecrawl", integration=integration, **kwargs)
        self._firecrawl_api_key: str | None = None # Cache for the API key
        if FirecrawlApiClient is None:
            logger.warning("Firecrawl SDK is not available. Firecrawl tools will not function.")

    @property
    def firecrawl_api_key(self) -> str:
        """
        Retrieves and caches the Firecrawl API key from the integration.
        Raises NotAuthorizedError if the key cannot be obtained.
        """
        if self._firecrawl_api_key is None:
            if not self.integration:
                logger.error(f"{self.name.capitalize()} App: Integration not configured.")
                raise NotAuthorizedError(
                    f"Integration not configured for {self.name.capitalize()} App. Cannot retrieve API key."
                )

            try:
                credentials = self.integration.get_credentials()
            except NotAuthorizedError as e:
                logger.error(f"{self.name.capitalize()} App: Authorization error when fetching credentials: {e.message}")
                raise # Re-raise the original NotAuthorizedError
            except Exception as e:
                logger.error(f"{self.name.capitalize()} App: Unexpected error when fetching credentials: {e}", exc_info=True)
                raise NotAuthorizedError(f"Failed to get {self.name.capitalize()} credentials: {e}")


            api_key = (
                credentials.get("api_key")
                or credentials.get("API_KEY") # Check common variations
                or credentials.get("apiKey")
            )

            if not api_key:
                logger.error(f"{self.name.capitalize()} App: API key not found in credentials.")
                action_message = (
                    f"API key for {self.name.capitalize()} is missing. "
                    "Please ensure it's set in the store via MCP frontend or configuration."
                )
                if hasattr(self.integration, 'authorize') and callable(self.integration.authorize):
                    try:
                        auth_details = self.integration.authorize()
                        if isinstance(auth_details, str):
                            action_message = auth_details
                        elif isinstance(auth_details, dict) and 'url' in auth_details:
                            action_message = f"Please authorize via: {auth_details['url']}"
                        elif isinstance(auth_details, dict) and 'message' in auth_details:
                            action_message = auth_details['message']
                    except Exception as auth_e:
                        logger.warning(f"Could not retrieve specific authorization action for {self.name.capitalize()}: {auth_e}")
                raise NotAuthorizedError(action_message)

            self._firecrawl_api_key = api_key
            logger.info(f"{self.name.capitalize()} API Key successfully retrieved and cached.")
        return self._firecrawl_api_key

    # Correct the return type hint to refer to the actual class name FirecrawlApp
    def _get_client(self) -> FirecrawlApp:
        """
        Initializes and returns the Firecrawl client after ensuring API key is set.
        Raises NotAuthorizedError if API key cannot be obtained or SDK is not installed.
        """
        if FirecrawlApiClient is None:
            logger.error("Firecrawl SDK (firecrawl-py) is not available.")
            raise ToolError("Firecrawl SDK (firecrawl-py) is not installed or failed to import.")

        # The property self.firecrawl_api_key will raise NotAuthorizedError if key is missing/unretrievable
        current_api_key = self.firecrawl_api_key
        # Since FirecrawlApiClient is the class FirecrawlApp when imported,
        # this correctly instantiates FirecrawlApp.
        return FirecrawlApiClient(api_key=current_api_key)

    def _handle_firecrawl_exception(self, e: Exception, operation_desc: str) -> str | None:
        """
        Handles exceptions from Firecrawl operations, raising NotAuthorizedError for auth issues
        and returning an error string or raising ToolError for other issues.
        This helper is designed to be used in tool methods.
        """
        logger.error(f"Firecrawl App: Error during {operation_desc}: {type(e).__name__} - {e}", exc_info=True)
        # Check for common authentication/authorization indicators
        error_str = str(e).lower()
        is_auth_error = (
            "unauthorized" in error_str or
            "api key" in error_str or
            "authentication" in error_str or
            (hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 401) or
            (hasattr(e, 'status_code') and e.status_code == 401) # some SDKs might attach status_code directly
        )
        if is_auth_error:
            raise NotAuthorizedError(f"Firecrawl API authentication/authorization failed for {operation_desc}: {e}")
  
        return f"Error during {operation_desc}: {type(e).__name__} - {e}"


    def scrape_url(
        self, url: str
    ) -> dict[str, Any] | str:
        """
        Scrapes a single URL using Firecrawl and returns the extracted data.

        Args:
            url: The URL of the web page to scrape.

        Returns:
            A dictionary containing the scraped data on success,
            or a string containing an error message on failure.
        
        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            scrape, important
        """
        logger.info(f"Attempting to scrape URL: {url}")
        try:
            client = self._get_client()
            response_data = client.scrape_url(url=url)
            logger.info(f"Successfully scraped URL: {url}")
            return response_data
        except NotAuthorizedError: 
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"scraping URL {url}")

    def search(
        self, query: str
    ) -> dict[str, Any] | str:
        """
        Performs a web search using Firecrawl's search capability.

        Args:
            query: The search query string.

        Returns:
            A dictionary containing the search results on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            search, important
        """
        logger.info(f"Attempting Firecrawl search for query: {query}")
        try:
            client = self._get_client()
            response = client.search(query=query)
            logger.info(f"Successfully performed Firecrawl search for query: {query}")
            return response
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"search for '{query}'")

    def start_crawl(
        self,
        url: str,
    ) -> dict[str, Any] | str:
        """
        Starts a async crawl job for a given URL using Firecrawl. Returns the job ID immediately.

        Args:
            url: The starting URL for the crawl.

        Returns:
            A dictionary containing the job initiation response on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            crawl, async_job, start
        """
        logger.info(f"Attempting to start Firecrawl crawl for URL: {url}")
        try:
            client = self._get_client()
            response = client.async_crawl_url(
                url=url,
            )
            job_id = response.id
            logger.info(f"Successfully started Firecrawl crawl for URL {url}, Job ID: {job_id}")
            return {"success": response.success, "id": response.id, "url": response.url}
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"starting crawl for URL {url}")

    def check_crawl_status(self, job_id: str) -> dict[str, Any] | str:
        """
        Checks the status of a previously initiated async Firecrawl crawl job.

        Args:
            job_id: The ID of the crawl job to check.

        Returns:
            A dictionary containing the job status details on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            crawl, async_job, status
        """
        logger.info(f"Attempting to check Firecrawl crawl status for job ID: {job_id}")
        try:
            client = self._get_client()
            status = client.check_crawl_status(id=job_id) # Corrected: job_id parameter name
            logger.info(f"Successfully checked Firecrawl crawl status for job ID: {job_id}")
            return status
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"checking crawl status for job ID {job_id}")

    def cancel_crawl(self, job_id: str) -> dict[str, Any] | str:
        """
        Cancels a currently running Firecrawl crawl job.

        Args:
            job_id: The ID of the crawl job to cancel.

        Returns:
            A dictionary confirming the cancellation status on success,
            or a string containing an error message on failure.
            (Note: This functionality might depend on Firecrawl API capabilities)

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed or operation not supported.

        Tags:
            crawl, async_job, management, cancel
        """
        logger.info(f"Attempting to cancel Firecrawl crawl job ID: {job_id}")
        try:
            client = self._get_client()
            response = client.cancel_crawl(id=job_id)
            logger.info(f"Successfully issued cancel command for Firecrawl crawl job ID: {job_id}")
            return response
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"cancelling crawl job ID {job_id}")

    def start_batch_scrape(
        self,
        urls: list[str],
    ) -> dict[str, Any] | str:
        """
        Starts a batch scrape job for multiple URLs using Firecrawl. (Note: May map to multiple individual scrapes or a specific batch API endpoint if available)

        Args:
            urls: A list of URLs to scrape.

        Returns:
            A dictionary containing the job initiation response (e.g., a batch job ID or list of results/job IDs) on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            scrape, batch, async_job, start
        """
        logger.info(f"Attempting to start Firecrawl batch scrape for {len(urls)} URLs.")
        try:
            client = self._get_client()
            response = client.async_batch_scrape_urls(urls=urls)
            logger.info(f"Successfully started Firecrawl batch scrape for {len(urls)} URLs.")
            return response
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"starting batch scrape for {len(urls)} URLs")

    def check_batch_scrape_status(self, job_id: str) -> dict[str, Any] | str:
        """
        Checks the status of a previously initiated Firecrawl batch scrape job.

        Args:
            job_id: The ID of the batch scrape job to check.

        Returns:
            A dictionary containing the job status details on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed or operation not supported.

        Tags:
            scrape, batch, async_job, status
        """
        logger.info(f"Attempting to check Firecrawl batch scrape status for job ID: {job_id}")
        try:
            client = self._get_client()
            status = client.check_batch_scrape_status(id=job_id)
            logger.info(f"Successfully checked Firecrawl batch scrape status for job ID: {job_id}")
            return status
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"checking batch scrape status for job ID {job_id}")

    def start_extract(
        self,
        urls: list[str],
        prompt: Optional[str] = None,
        schema: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        allow_external_links: Optional[bool] = False,
    ) -> dict[str, Any] | str:
        """
        Starts an asynchronous extraction job for one or more URLs using Firecrawl.

        Args:
            urls: A list of URLs to extract data from.
            prompt: Optional custom extraction prompt.
            schema: Optional JSON schema or Pydantic model for the desired output structure.
            system_prompt: Optional system context for the extraction.
            allow_external_links: Optional boolean to allow following external links.

        Returns:
            A dictionary containing the job initiation response on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed.

        Tags:
            extract, ai, async_job, start
        """
        logger.info(f"Attempting to start Firecrawl extraction for {len(urls)} URLs with prompt: {prompt is not None}, schema: {schema is not None}.")
        try:
            client = self._get_client()
            response = client.async_extract(
                urls=urls,
                prompt=prompt,
                schema=schema,
                system_prompt=system_prompt,
                allow_external_links=allow_external_links,
            )
            logger.info(f"Successfully started Firecrawl extraction for {len(urls)} URLs. Job ID: {response.job_id}")
            return response.model_dump()
        except NotAuthorizedError:
            logger.error("Firecrawl API key missing or invalid.")
            raise
        except ToolError:
            logger.error("Firecrawl SDK not installed.")
            raise
        except Exception as e:
            error_message = self._handle_firecrawl_exception(e, f"starting extraction for {len(urls)} URLs")
            logger.error(f"Failed to start Firecrawl extraction: {error_message}")
            return error_message

    def check_extract_status(self, job_id: str) -> dict[str, Any] | str:
        """
        Checks the status of a previously initiated Firecrawl extraction job.

        Args:
            job_id: The ID of the extraction job to check.

        Returns:
            A dictionary containing the job status details on success,
            or a string containing an error message on failure.

        Raises:
            NotAuthorizedError: If API key is missing or invalid.
            ToolError: If the Firecrawl SDK is not installed or operation not supported.

        Tags:
            extract, ai, async_job, status
        """
        logger.info(f"Attempting to check Firecrawl extraction status for job ID: {job_id}")
        try:
            client = self._get_client()
            status = client.get_extract_status(job_id=job_id)
            logger.info(f"Successfully checked Firecrawl extraction status for job ID: {job_id}")
            return status
        except NotAuthorizedError:
            raise
        except ToolError:
            raise
        except Exception as e:
            return self._handle_firecrawl_exception(e, f"checking extraction status for job ID {job_id}")

    def list_tools(self):
        return [
            self.scrape_url,
            self.search,
            self.start_crawl,
            self.check_crawl_status,
            self.cancel_crawl,
            self.start_batch_scrape, 
            self.check_batch_scrape_status, 
            self.start_extract, 
            self.check_extract_status, 
        ]