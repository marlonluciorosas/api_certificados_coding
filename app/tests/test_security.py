"""Testes das funções de segurança (senha e token)."""
from __future__ import annotations

import unittest

from ..core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class SenhaTests(unittest.TestCase):
    def test_hash_e_diferente_da_senha(self) -> None:
        hash_gerado = hash_password("senha123")
        self.assertNotIn("senha123", hash_gerado)
        self.assertEqual(hash_gerado.count("$"), 3)

    def test_mesma_senha_gera_hashes_diferentes(self) -> None:
        """O "sal" aleatório faz dois hashes da mesma senha serem diferentes."""
        self.assertNotEqual(hash_password("senha123"), hash_password("senha123"))

    def test_verificacao_de_senha(self) -> None:
        hash_gerado = hash_password("senha123")
        self.assertTrue(verify_password("senha123", hash_gerado))
        self.assertFalse(verify_password("senha124", hash_gerado))

    def test_hash_estranho_nao_quebra_o_sistema(self) -> None:
        self.assertFalse(verify_password("senha123", ""))
        self.assertFalse(verify_password("senha123", "texto-sem-formato"))


class TokenTests(unittest.TestCase):
    def test_token_guarda_o_id_do_usuario(self) -> None:
        token = create_access_token(42)
        self.assertEqual(decode_access_token(token), 42)

    def test_token_expirado_e_recusado(self) -> None:
        token = create_access_token(7, expires_minutes=-1)
        with self.assertRaises(TokenError):
            decode_access_token(token)

    def test_token_adulterado_e_recusado(self) -> None:
        token = create_access_token(7)
        payload, assinatura = token.split(".")
        with self.assertRaises(TokenError):
            decode_access_token(f"{payload}.{assinatura[:-2]}xx")

    def test_texto_qualquer_e_recusado(self) -> None:
        with self.assertRaises(TokenError):
            decode_access_token("isso-nao-e-um-token")


if __name__ == "__main__":
    unittest.main(verbosity=2)