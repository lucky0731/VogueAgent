"""POST /image-search: lookalike retrieval from a photo."""
from conftest import jpeg


def search(client, data, name="photo.jpg", ctype="image/jpeg"):
    return client.post("/image-search", files={"image": (name, data, ctype)}).json()


def names(reply):
    return [p["name"] for p in reply["data"]]


def test_blue_shirt_photo_finds_blue_shirts_first(client):
    reply = search(client, jpeg((125, 175, 225)))
    assert reply["type"] == "products"
    assert reply["message"] == "Here are styles similar to your blue shirt."
    assert names(reply)[0] == "Sky Blue Linen Shirt"
    assert "Red Floral Dress" not in names(reply) and "Kids Dino Pyjamas" not in names(reply)


def test_garment_type_and_colour_both_count(client, fake_llm):
    fake_llm.vision_tags = {"is_clothing": True, "garment_type": "dress", "category": "women", "colors": ["red"]}
    assert names(search(client, jpeg((205, 35, 45))))[0] == "Red Floral Dress"


def test_results_are_ready_for_cards(client):
    product = search(client, jpeg((125, 175, 225)))["data"][0]
    assert len(product["id"]) == 24 and product["image"].startswith("data:image/jpeg")
    assert not {"_hist", "_id", "image_data"} & product.keys()


def test_photo_is_sent_to_the_vision_model_as_a_data_url(client, fake_llm):
    search(client, jpeg((125, 175, 225), size=(3000, 4000)))
    model, kwargs = fake_llm.calls[0]
    assert model == "qwen/qwen3.8-27b"
    assert kwargs["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert kwargs["response_format"] == {"type": "json_object"}


def test_not_clothing(client, fake_llm):
    fake_llm.vision_tags = {"is_clothing": False}
    reply = search(client, jpeg((0, 200, 0)))
    assert reply["type"] == "text" and "couldn't spot any clothing" in reply["message"]


def test_vision_outage_falls_back_to_colour(client, fake_llm):
    fake_llm.fail = {"qwen/qwen3.8-27b"}
    reply = search(client, jpeg((205, 35, 45)))
    assert reply["message"] == "Here are pieces in similar colours."
    assert names(reply)[0] == "Red Floral Dress"


def test_not_an_image(client):
    assert "doesn't look like a photo" in search(client, b"hello", "notes.txt", "text/plain")["message"]


def test_too_large(client):
    assert "larger than 8 MB" in search(client, b"\xff\xd8" + b"0" * (9 * 1024 * 1024))["message"]
