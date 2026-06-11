import pytest

from irisflow.storage.phrases_store import PhrasesStore


def test_carrega_categorias_padrao(tmp_phrases_dir):
    store = PhrasesStore(path=tmp_phrases_dir / "phrases.json")
    categorias = store.get_categories()

    assert len(categorias) > 0, "deve haver categorias padrão"
    for cat in categorias:
        assert "id" in cat
        assert "nome" in cat
        assert "icone" in cat
        assert "frases" in cat


def test_get_frases_de_categoria(tmp_phrases_dir):
    store = PhrasesStore(path=tmp_phrases_dir / "phrases.json")
    frases = store.get_phrases("saude")

    assert len(frases) > 0, "categoria 'saude' deve ter frases"
    assert all(isinstance(f, str) and f for f in frases), "todas as frases devem ser strings não vazias"


def test_adicionar_frase(tmp_phrases_dir):
    store = PhrasesStore(path=tmp_phrases_dir / "phrases.json")
    store.add_phrase("saude", "Nova frase de teste")

    assert "Nova frase de teste" in store.get_phrases("saude")


def test_frase_persiste(tmp_phrases_dir):
    path = tmp_phrases_dir / "phrases.json"
    store1 = PhrasesStore(path=path)
    store1.add_phrase("social", "Frase persistida")

    store2 = PhrasesStore(path=path)
    assert "Frase persistida" in store2.get_phrases("social")


def test_remover_frase(tmp_phrases_dir):
    store = PhrasesStore(path=tmp_phrases_dir / "phrases.json")
    frase = "Frase para remover"

    store.add_phrase("saude", frase)
    assert frase in store.get_phrases("saude")

    store.remove_phrase("saude", frase)
    assert frase not in store.get_phrases("saude")


def test_categoria_inexistente_retorna_lista_vazia(tmp_phrases_dir):
    store = PhrasesStore(path=tmp_phrases_dir / "phrases.json")
    assert store.get_phrases("categoria_que_nao_existe") == []
