from app.services.norm_page_locator import NormLocateRequest, NormPageLocator


def test_norm_page_locator_locate_many_finds_ranges_in_order():
    locator = NormPageLocator()
    requests = [
        NormLocateRequest(label="1.0.1", title="总则内容。"),
        NormLocateRequest(label="1.1.1", title="范围内容。"),
        NormLocateRequest(label="4.1.3", title="三维冲击加速度应控制在3g左右。"),
    ]

    ranges = locator.locate_many(
        requests=requests,
        page_texts=[
            {"page": 1, "text": "1 总则 1.0.1 总则内容。"},
            {"page": 2, "text": "1.1 范围 1.1.1 范围内容。"},
            {"page": 31, "text": "4.1 装卸、运输与就位 4.1.3 三维冲击加速度应控制在3g左右。"},
        ],
    )

    assert ranges["1.0.1"] == (1, 1)
    assert ranges["1.1.1"] == (2, 30)
    assert ranges["4.1.3"] == (31, 31)


def test_norm_page_locator_respects_page_window_bounds():
    locator = NormPageLocator()
    ranges = locator.locate_many(
        requests=[NormLocateRequest(label="4.1.3", title="三维冲击加速度")],
        page_texts=[
            {"page": 10, "text": "4.1.3 三维冲击加速度应控制在3g左右。"},
        ],
        page_min=20,
        page_max=30,
    )

    assert ranges["4.1.3"] == (None, None)

