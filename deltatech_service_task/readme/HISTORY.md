## 19.0.0.0.20

- Tip de mentenanță (`service.maintenance.type`, ex. primăvară / toamnă / intermediară), listă
  gestionată de utilizator în Configurare.
- Operațiunile (Parts / Checks / Measurements) din șablonul tipului de echipament și de pe echipament
  se pot marca cu unul sau mai multe tipuri de mentenanță; nemarcat = valabil la toate.
- Marcajul se copiază din șablon pe echipament ca valoare: ajustarea pe un echipament nu atinge
  șablonul și nici celelalte echipamente.
- Sarcina are câmpul Tip mentenanță; la preluarea operațiunilor de pe echipament se copiază doar cele
  valabile pentru tipul sarcinii. Subsarcinile moștenesc tipul lucrării-părinte.
