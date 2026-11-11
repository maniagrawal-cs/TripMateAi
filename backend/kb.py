"""Destination knowledge base (RAG source), quiz bank and missions for the demo destination."""
TAJ = {
 "name": "Taj Mahal, Agra, India", "lat": 27.1751, "lng": 78.0421,
 "sections": {
  "history": "The Taj Mahal was commissioned in 1632 by Mughal emperor Shah Jahan as a mausoleum for his wife Mumtaz Mahal, who died in 1631 while giving birth to their 14th child.",
  "construction": "Construction of the main mausoleum was largely complete around 1643, and the wider complex took until about 1653. Thousands of artisans and labourers worked on it. Ustad Ahmad Lahori is traditionally named as the lead architect. White marble came from Makrana in Rajasthan, and gemstones for inlay came from across Asia.",
  "architecture": "The Taj Mahal blends Persian, Islamic and Indian styles. It stands on a raised platform with four minarets, a central double dome and four-fold symmetry. The minarets lean slightly outward, which is commonly explained as protecting the tomb if one fell. The complex follows a charbagh (four-part) garden layout.",
  "decoration": "Walls feature pietra dura: fitted semi-precious stones inlaid in marble to form floral designs. There are also carved marble reliefs, jali (perforated screens) and Quranic calligraphy whose letters are scaled so they look equal in size from the ground.",
  "marble": "Marble is a metamorphic rock formed from limestone. It is translucent, so light penetrates slightly, and the Taj appears pinkish at dawn, white at midday and golden at sunset.",
  "culture": "The Taj Mahal is a symbol of love and a masterpiece of Mughal art. It was inscribed as a UNESCO World Heritage Site in 1983. It stands on the bank of the Yamuna river in Agra.",
  "conservation": "Air pollution can yellow the marble, so vehicles are restricted near the monument and mud-pack cleaning treatments are used periodically.",
  "nearby": "Nearby: Agra Fort (UNESCO site), Mehtab Bagh garden across the Yamuna, Itimad-ud-Daulah's tomb, and Fatehpur Sikri.",
 },
 "timeline": [["1631","Mumtaz Mahal dies"],["1632","Construction begins"],["1643","Main mausoleum largely complete"],["1653","Whole complex complete"],["1983","UNESCO World Heritage Site"]],
 "facts": ["The four minarets lean slightly outward.", "The marble changes colour through the day.", "The mausoleum is a symmetrical design."],
 "subjects": ["History", "Mathematics (symmetry)", "Physics (light and reflection)", "Geography", "Art"],
 "sources": [["UNESCO World Heritage Centre: Taj Mahal", "https://whc.unesco.org/en/list/252"],
             ["Archaeological Survey of India", "https://asi.nic.in"]],
}
def mc(t, o, a, e, tp): return dict(qtype="mcq", text=t, options=o, answer=a, explanation=e, topic=tp)
def tf(t, a, e, tp): return dict(qtype="tf", text=t, options=["True", "False"], answer=a, explanation=e, topic=tp)
def sa(t, a, e, tp): return dict(qtype="short", text=t, options=[], answer=a, explanation=e, topic=tp)
QUIZ_BANK = [
 mc("Who commissioned the Taj Mahal?", ["Akbar","Shah Jahan","Aurangzeb","Babur"], "Shah Jahan", "Shah Jahan built it for Mumtaz Mahal.", "History"),
 mc("For whom was the Taj Mahal built?", ["Nur Jahan","Mumtaz Mahal","Jahanara","Razia"], "Mumtaz Mahal", "It is her mausoleum.", "History"),
 mc("In which city is the Taj Mahal?", ["Delhi","Jaipur","Agra","Lucknow"], "Agra", "It is on the Yamuna in Agra.", "Geography"),
 mc("Which river flows beside the Taj Mahal?", ["Ganga","Yamuna","Narmada","Chambal"], "Yamuna", "The monument stands on the Yamuna's bank.", "Geography"),
 mc("What is the main material of the mausoleum?", ["Red sandstone","Granite","White marble","Limestone"], "White marble", "Makrana marble was used.", "Architecture"),
 tf("The minarets lean slightly outward.", "True", "A commonly cited reason is protecting the tomb in case of collapse.", "Architecture"),
 tf("The Taj Mahal was completed within one year.", "False", "The complex took more than 20 years.", "History"),
 mc("Inlay of coloured stones in marble is called:", ["Fresco","Pietra dura","Mosaic glaze","Batik"], "Pietra dura", "Pietra dura creates floral patterns.", "Art"),
 mc("The Taj Mahal became a UNESCO World Heritage Site in:", ["1950","1983","1999","2007"], "1983", "Inscribed in 1983.", "Culture"),
 sa("Name the type of four-part garden layout around the Taj Mahal.", "charbagh", "A charbagh divides the garden into four parts.", "Architecture"),
 tf("Marble is a metamorphic rock.", "True", "It forms from limestone under heat and pressure.", "Science"),
 sa("What kind of symmetry does the Taj Mahal show: bilateral or none?", "bilateral", "Its two halves mirror each other.", "Mathematics"),
]
MISSIONS = [
 dict(title="The Hidden Floral Art", task="Find a floral decorative pattern on the monument and photograph it.", criteria="A floral decorative pattern, such as pietra dura inlay or carved flowers, is clearly visible.", hint="Look low on the walls near the doorways and cenotaph panels.", points=20, difficulty="easy"),
 dict(title="Minaret Spotter", task="Photograph one of the four minarets.", criteria="A tall slender minaret tower is clearly visible.", hint="Stand at the corner of the platform and look up.", points=20, difficulty="easy"),
 dict(title="Perfect Symmetry", task="Take a photo showing the symmetry of the monument.", criteria="The photo shows the monument or a part of it with clear mirror symmetry.", hint="Stand on the central axis by the long reflecting pool.", points=25, difficulty="medium", game="find_feature"),
 dict(title="Calligraphy Detective", task="Photograph Arabic calligraphy on the entrance arch.", criteria="Arabic or Persian calligraphic inscription is visible.", hint="Check the great gate and the arches around the mausoleum.", points=30, difficulty="hard", game="mystery"),
]
