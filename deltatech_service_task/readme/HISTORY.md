## 20.0.0.0.24 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.0.0.23 (2026-10-15)

- Apps Store main image regenerated with the redrawn module icon.

## 19.0.0.0.22 (2026-10-15)

- Module icon redrawn in the Terrabit house style: clean vector, 100x100 viewBox, no embedded image.

## 19.0.0.0.21 (2026-10-03)

- Task parts, checks and measurements did not follow the access rules of their task:
  a project user could search, read, modify or delete them for tasks of other
  companies or of private projects. They now follow their task: reading requires
  read access on the task; creating, modifying, deleting or moving a line to another
  task requires write access on the task. Searches and counts return only the lines
  of tasks the user can read.

## 19.0.0.0.20

- Tip de mentenanță (`service.maintenance.type`, ex. primăvară / toamnă / intermediară), listă
  gestionată de utilizator în Configurare.
- Operațiunile (Parts / Checks / Measurements) din șablonul tipului de echipament și de pe echipament
  se pot marca cu unul sau mai multe tipuri de mentenanță; nemarcat = valabil la toate.
- Marcajul se copiază din șablon pe echipament ca valoare: ajustarea pe un echipament nu atinge
  șablonul și nici celelalte echipamente.
- Sarcina are câmpul Tip mentenanță; la preluarea operațiunilor de pe echipament se copiază doar cele
  valabile pentru tipul sarcinii. Subsarcinile moștenesc tipul lucrării-părinte.
