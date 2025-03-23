import asyncio
import re
from dataclasses import dataclass
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from src.helpers.logger import logger


@dataclass
class ParseResult:
    """Classe para armazenar o resultado do parsing"""

    content: Optional[str]
    method: str
    success: bool
    error: Optional[str] = None
    is_position_closed: bool = False


class JobDescriptionParser:
    """Classe para gerenciar diferentes estratégias de parsing"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        self.content_selectors = [
            'div[class*="job-description"]',
            'div[class*="description"]',
            'div[class*="posting"]',
            'div[class*="content"]',
            "article",
            "main",
            '[role="main"]',
            ".job-details",
            "#job-details",
        ]

    async def is_url(self, text: str) -> bool:
        """Verifica se o texto é uma URL válida"""
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return bool(url_pattern.match(text))

    def clean_text(self, text: str) -> str:
        """Limpa e formata o texto extraído"""
        if not text:
            return ""

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[\n\r\t]", " ", text)
        text = re.sub(r"[^\w\s.,!?-]", "", text)

        return text.strip()

    def is_job_finished(self, text: str) -> bool:
        """Verify if the job position is closed"""
        normalized_text = text.lower()

        closed_indicators = [
            "this role is currently no longer accepting new applications",
            "vaga encerrada",
            "não estamos mais aceitando candidaturas",
            "processo seletivo encerrado",
            "applications closed",
            "position filled",
            "we are no longer accepting applications",
        ]

        for indicator in closed_indicators:
            if indicator in normalized_text:
                return True

    def extract_text_from_html(
        self, html_content: str, selectors: list
    ) -> Optional[str]:
        """Extrai texto do HTML usando BeautifulSoup"""
        soup = BeautifulSoup(html_content, "html.parser")

        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.decompose()

        for selector in selectors:
            try:
                content = soup.select_one(selector)
                if content:
                    return content.get_text(separator=" ", strip=True)
            except Exception:
                continue

        if soup.body:
            return soup.body.get_text(separator=" ", strip=True)

        return None

    async def try_simple_request(self, url: str) -> ParseResult:
        """Tenta fazer uma requisição HTTP simples"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=self.headers, timeout=10
                ) as response:
                    if response.status != 200:
                        return ParseResult(
                            None,
                            "simple_request",
                            False,
                            f"Status code: {response.status}",
                        )

                    html_content = await response.text()
                    text = self.extract_text_from_html(
                        html_content, self.content_selectors
                    )

                    if text and len(text) > 100:
                        return ParseResult(
                            self.clean_text(text),
                            "simple_request",
                            True,
                            None,
                            self.is_job_finished(text),
                        )

                    return ParseResult(
                        None, "simple_request", False, "Conteúdo insuficiente"
                    )
        except Exception as e:
            return ParseResult(None, "simple_request", False, str(e))

    async def try_playwright(self, url: str) -> ParseResult:
        """Tenta usar Playwright para renderizar JavaScript"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle")
                await asyncio.sleep(2)

                for selector in self.content_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            content = await element.inner_text()
                            if content and len(content) > 100:
                                await browser.close()
                                return ParseResult(
                                    self.clean_text(content), "playwright", True
                                )
                    except Exception:
                        continue

                content = await page.content()
                text = self.extract_text_from_html(content, self.content_selectors)
                await browser.close()

                if text and len(text) > 100:
                    return ParseResult(
                        self.clean_text(text),
                        "playwright",
                        True,
                        None,
                        self.is_job_finished(text),
                    )

                return ParseResult(None, "playwright", False, "Conteúdo insuficiente")

        except Exception as e:
            return ParseResult(None, "playwright", False, str(e))

    async def parse(self, text: str) -> Optional[str]:
        """Método principal para fazer parse do conteúdo"""
        if not await self.is_url(text):
            return text

        logger.send_log(f"Iniciando parse da URL: {text}")

        result = await self.try_simple_request(text)
        logger.send_log(f"Resultado simple_request: {result.success}")

        if result.success:
            return result.content

        logger.send_log("Trying with Playwright...")
        result = await self.try_playwright(text)
        logger.send_log(f"Resultado playwright: {result.success}")

        if result.success:
            return result.content

        logger.send_error("Todas as tentativas falharam")
        return None


parser = JobDescriptionParser()


async def parse_job_description(text: str) -> Optional[str]:
    """Function to parse job description"""
    return await parser.parse(text)
