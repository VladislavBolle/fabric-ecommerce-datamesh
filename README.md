# E-Commerce-Datenplattform auf Microsoft Fabric

**Data Mesh & Medaillon-Architektur — von Rohdaten zu Dashboards und Machine Learning.**

<sub>Repository: `fabric-ecommerce-datamesh`</sub>

Dieses Repository ist ein **Referenz- und Portfolioprojekt**. Es baut eine vollständige, unternehmensnahe Datenplattform von Grund auf — durchgängig im **Microsoft-Data-Ökosystem** rund um **Microsoft Fabric**, **Azure** und **Power BI**. Aus öffentlichen E-Commerce-Rohdaten entstehen Schritt für Schritt bereinigte Tabellen, ein für Auswertungen optimiertes Datenmodell, ein Machine-Learning-Modell und (geplant) ein Dashboard.

Der Zweck ist nicht das Ergebnis allein, sondern das *Wie* und *Warum*. Das Projekt zeigt an einem realistischen End-to-End-Beispiel, wie die einzelnen Fabric-Dienste zusammenspielen und nach welchen Überlegungen man eine Datenplattform strukturiert. Es dient damit als **nachvollziehbares Beispiel**, wie man im Microsoft-Stack Architekturentscheidungen trifft *und begründet* — einschließlich der Stellen, an denen ein Portfolio bewusst vereinfacht und ein echtes Produktivprojekt weitergehen müsste.

Zwei etablierte Muster geben die Struktur vor:

- **Data Mesh** beantwortet die *organisatorische* Frage: Wer besitzt welche Daten? Antwort: dezentrale Verantwortung in fachlichen Bereichen statt eines einzigen zentralen Datenteams.
- **Medaillon-Architektur** beantwortet die *technische* Frage: Wie reifen Daten von roh zu servierfertig? Antwort: in drei aufeinander aufbauenden Schichten — Bronze → Silber → Gold.

---

## Der Microsoft-Stack in diesem Projekt

Alles läuft in der Microsoft-Welt. Das Herzstück ist **Microsoft Fabric** — eine integrierte Cloud-Plattform (SaaS), die Datenaufbereitung, Data Warehousing, Data Science und Business Intelligence unter einem Dach und auf *einem* gemeinsamen Speicher vereint. Azure liefert nur den vorgelagerten Rohdaten-Speicher, Power BI ist am Ende die Ansichts-Ebene.

Damit die späteren Abschnitte verständlich sind, hier zuerst die **Bausteine** und wofür sie hier eingesetzt werden. Man muss sie noch nicht im Detail verstehen — es reicht, den Namen einmal gehört zu haben; im weiteren Verlauf tauchen sie in ihrem Zusammenhang wieder auf.

| Baustein | Was es ist | Rolle in diesem Projekt |
|---|---|---|
| **Azure Data Lake Storage Gen2** | Cloud-Objektspeicher in Azure (Dateien in „Containern") | Landing Zone für die neun Roh-CSVs — der einzige Teil *außerhalb* von Fabric |
| **OneLake** | Der eine, einheitliche Data Lake für ganz Fabric — quasi „das OneDrive für Daten" | Speichert alle Tabellen und Dateien der Plattform, offen im Delta-/Parquet-Format |
| **Lakehouse** | Verbindet Data Lake (Dateien) und Datenbank (Tabellen); per Spark **und** SQL lesbar | Beheimatet **Bronze** und **Silber** — die Engineering-Schichten |
| **Warehouse** | Klassisches T-SQL-Data-Warehouse mit Lese- **und Schreib**zugriff | Beheimatet **Gold** — die Serving-Schicht für BI |
| **Spark / PySpark** | Verteilte Engine, um große Datenmengen in Code (Python) zu verarbeiten | Bereinigt die Rohdaten und schreibt die Silber-Tabellen |
| **Delta-Tabellen (Delta Lake)** | Offenes Tabellenformat auf Parquet mit Transaktions-Log — ACID, Zeitreise, Schema-Kontrolle | Das Standard-Tabellenformat in OneLake |
| **Data Factory / Pipelines** | Orchestrierung und Datenbewegung (Copy-Aktivität, Ablauflogik, Zeitplan) | Holt die Rohdaten herein (Ingestion) und steuert den Gold-Build |
| **Notebooks** | Interaktive Code-Oberfläche (PySpark, SQL, Python) | Silber-Transformationen und das ML-Modell |
| **OneLake Shortcuts** | Virtuelle Verweise auf Daten an anderer Stelle — ohne physische Kopie („zero-copy") | Teilen von Datenprodukten zwischen Workspaces und Domänen |
| **Domains (Domänen)** | Fachliche Gruppierung von Workspaces im Fabric-Admin-Portal | Bilden die Data-Mesh-Domänen ab |
| **Workspaces** | Container für Fabric-Inhalte und zugleich die Berechtigungs-/Ownership-Grenze | Ein Workspace je Subdomäne |
| **Semantic Model + Direct Lake** | Power-BI-Datenmodell, das Delta-Tabellen *direkt* aus OneLake liest — ohne Import, ohne DirectQuery | Grundlage des geplanten Dashboards |
| **Power BI** | Berichte und Dashboards | Die Konsumschicht für die Gold-Daten *(geplant)* |
| **MLflow** | In Fabric integriertes Experiment-Tracking | Protokolliert und vergleicht die ML-Trainingsläufe |
| **Git-Integration** | Versionierung der Fabric-Inhalte über GitHub | Mono-Repo, ein Ordner je Workspace |

Der rote Faden hinter dieser Auswahl ist, dass jede Aufgabe ihr passendes Werkzeug bekommt, ohne die Plattform zu verlassen: Datei-Ingestion über **Data Factory**, code-getriebenes Engineering über **Spark/Notebooks** im **Lakehouse**, kuratiertes Serving über **T-SQL** im **Warehouse**, geteilte Nutzung über **Shortcuts** statt Kopien, und BI über **Direct Lake** ohne teures Nachladen. Der gemeinsame Nenner ist **OneLake** und das offene **Delta**-Format — dadurch sieht jeder Dienst dieselben Daten, ohne dass man sie zwischen Silos hin- und herschieben muss. Genau dieses „ein Speicher, viele Engines" ist der Kerngedanke von Fabric, und dieses Projekt spielt ihn bewusst durch.

---

## 1. Warum diese Architektur? Ein Blick zurück

Datenarchitekturen haben sich schon immer an der jeweils *knappsten* Ressource ausgerichtet. Was teuer war, wurde geschont — und daraus wurden die „Best Practices" ihrer Zeit. Als Speicher teuer war, baute man Modelle, die Redundanz um jeden Preis vermieden: stark normalisiert, jede Information genau einmal abgelegt. Als der Engpass eher bei Arbeitsspeicher und Rechenzeit lag, drehte sich vieles darum, Daten möglichst effizient in den RAM zu bekommen und dort zu halten.

Heute hat sich dieses Verhältnis verschoben. Speicher ist billig geworden (auch wenn er zuletzt wieder etwas anzieht), und die Rechenleistung ist der Posten, der in der Cloud tatsächlich ins Gewicht fällt. Entscheidend ist dabei nie der absolute Preis, sondern das *Verhältnis* zwischen Speicher, RAM, CPU und Energie — genau dieses Verhältnis bestimmt, was zu einem gegebenen Zeitpunkt als gute Architektur gilt.

Aus der verschobenen Kostenstruktur folgt ein konkreter Umbau. Weil Speicher kaum noch etwas kostet, kann man es sich leisten, Daten erst einmal *roh und vollständig* abzulegen und sie erst danach zu transformieren — der Wechsel von ETL zu **ELT** (Extract-Load-Transform statt Extract-Transform-Load). Man optimiert nicht mehr, *was* man sich überhaupt zu speichern leisten kann, sondern *was und wann* man rechnet. Das ist zugleich der Grund, warum eine rohe, unveränderte Bronze-Schicht überhaupt sinnvoll ist und warum man sich die bewusste Datenverdopplung der späteren Schichten leisten kann. In der Ära des teuren Speichers hätte man beides vermieden.

So weit die technische Seite. Mindestens ebenso prägend — und der eigentliche Grund für den Aufbau dieses Projekts — ist die *organisatorische* Seite.

Lange gab es dafür nur ein Modell: ein zentrales Datenteam, das praktisch alles übernimmt. Es sammelt die Anforderungen aller Fachbereiche ein, übersetzt sie, lädt und transformiert die Daten, stellt Auswertungen und Dashboards bereit, holt Feedback ein, testet und validiert. Der Fachbereich äußert im Grunde nur seine Wünsche und beurteilt am Ende, ob ihm das Ergebnis gefällt — ohne je selbst technisch Hand anzulegen. Das hat lange getragen, und eine Zeit lang war es alternativlos: Die Werkzeuge waren so komplex und so schwer zugänglich, dass ein spezialisiertes Team schlicht notwendig war.

Dann kam Self-Service. Werkzeuge wie **Power BI** — und heute die gesamte Fabric-Plattform — traten mit einer anderen Prämisse an: *Es geht auch anders.* Daten werden leichter zugänglich und abrufbar, und auch Menschen ohne tiefes Engineering-Wissen können mit Low-Code- und No-Code-Mitteln selbst etwas bauen, oft per Drag-and-Drop.

In der Praxis ist dieser Anspruch vielerorts gegen die Wand gefahren — nicht an der Technik, sondern an der Organisation. Die alte, historisch gewachsene Zentralstruktur blieb bestehen, und der Self-Service kam einfach obendrauf. Beides zusammen passt nicht: Auf der einen Seite baut das zentrale Team weiter für alle, mit Governance mal mehr, mal weniger; auf der anderen ziehen einzelne Bereiche parallel ihre eigenen Lösungen hoch. Das Ergebnis ist ein Wildwuchs, in dem sich Kennzahlen widersprechen, Dinge doppelt entstehen und alles langsam und mühsam vorangeht. Mittendrin, als Engpass, durch den am Ende fast jede Anforderung muss, sitzt weiterhin das zentrale Datenteam.

![Der Bottleneck: ein zentrales Datenteam bremst alle Abteilungen aus](docs/01-bottleneck.png)

Damit ist das eigentliche Problem benannt, und es ist kein technisches. Die Technik *ist* da. Was fehlt, ist eine bewusste **Architektur- und Organisationsentscheidung**, die den Self-Service-Gedanken tatsächlich einlöst, statt ihn auf eine Struktur zu setzen, die ihn ausbremst. Genau hier setzt **Data Mesh** an: Verantwortung dorthin verlagern, wo das fachliche Wissen sitzt, ohne ins alte Chaos zurückzufallen. Das ist keine Universallösung — für ein kleines Unternehmen mit wenigen Quellen bleibt ein zentrales Team schneller und günstiger. Es lohnt sich dort, wo viele Bereiche parallel Daten produzieren und konsumieren und der zentrale Engpass real wehtut. Wie Data Mesh das konkret leistet, zeigt der nächste Abschnitt.

---

## 2. Was ist Data Mesh?

Statt einer zentralen Datenküche, die für alle kocht, bekommt **jede Abteilung ihre eigene kleine Küche** — betreibt sie aber nach gemeinsamen Standards. Jede Abteilung ist für ihre eigenen Daten verantwortlich und stellt sie den anderen als fertiges, verlässliches **„Datenprodukt"** zur Verfügung — so wie ein Team im Supermarkt ein fertig verpacktes Produkt ins Regal stellt, das andere einfach nehmen können.

![Zentralisiert vs. Data Mesh: von einem Team für alle zu Datenprodukten pro Domäne](docs/02-centralized-vs-mesh.png)

Data Mesh beruht auf vier Prinzipien:

1. **Domain Ownership** — fachliche Bereiche besitzen ihre Daten und verantworten deren Qualität.
2. **Data as a Product** — Daten werden wie ein Produkt gepflegt und bereitgestellt (mit Dokumentation, verlässlichem Schema, klarer Zuständigkeit).
3. **Self-Serve-Plattform** — eine gemeinsame technische Basis, auf der alle Bereiche bauen, ohne das Rad neu zu erfinden.
4. **Föderierte Governance** — gemeinsame Regeln (Namensgebung, Sicherheit, Standards), aber dezentrale Umsetzung.

**Der Vorteil** liegt auf der Hand: Verantwortung sitzt dort, wo das Fachwissen ist, und Bereiche können unabhängig voneinander arbeiten. **Der Preis dafür** ist mehr Abstimmung — ohne gemeinsame Standards driften die Bereiche auseinander und man tauscht einen zentralen Engpass gegen viele kleine Datensilos. Data Mesh ist deshalb *kein* „jeder macht sein eigenes Ding", sondern dezentrale Verantwortung **plus** zentral vereinbarte Leitplanken.

In Microsoft Fabric bilde ich diese Prinzipien konkret ab über **Fabric Domains** (fachliche Gruppierung), **einen Workspace pro Subdomäne** (Ownership-Grenze) und **OneLake Shortcuts** (Datenprodukte werden ohne Kopie geteilt — „zero-copy"). Die Self-Serve-Plattform ist Fabric selbst; die Governance regeln später Zugriffsrollen. Wichtig: Ich baue bewusst einen **hybriden** Ansatz — eine geteilte zentrale Ingestion für Rohdaten, aber domänen-eigene Verarbeitung. Das vermeidet, dass jede Domäne dieselbe Quelle mehrfach lädt, und hält trotzdem das Ownership dort, wo es zählt. Reine Data-Mesh-Lehre würde die Ingestion in die jeweilige Quell-Domäne verlagern; bei nur einer Quelle wäre das hier unnötiger Overhead — eine bewusste Abweichung, kein Versehen.

---

## 3. Die Medaillon-Architektur: Bronze, Silber, Gold

Rohdaten sind selten direkt auswertbar: Formate sind uneinheitlich, Werte fehlen oder widersprechen sich, und die Struktur folgt dem Quellsystem statt der späteren Auswertung. Die Medaillon-Architektur bringt die Daten deshalb in drei aufeinander aufbauenden Schichten in Form, jede mit einem klaren Zweck:

- 🥉 **Bronze** — die Rohdaten, exakt so übernommen, wie sie ankommen (unverändert, für Nachvollziehbarkeit und Wiederholbarkeit).
- 🥈 **Silber** — bereinigt, typisiert und dedupliziert; verlässliche Tabellen, aber noch nah an der Quelle.
- 🥇 **Gold** — für die Nutzung modelliert und aufbereitet, optimiert für Auswertungen und Dashboards.

![Medaillon-Architektur: von rohen Daten über bereinigte bis zu servierfertigen Daten](docs/03-medallion.png)

Die drei Schichten trennen Verantwortlichkeiten. **Bronze** bewahrt die Rohdaten unverändert — wichtig für Nachvollziehbarkeit und Wiederholbarkeit: Findet man später einen Fehler in der Bereinigung, kann man jederzeit auf das Original zurück, ohne die Quelle erneut anzufragen. **Silber** enthält bereinigte, typisierte Tabellen (eine pro Quell-Entität), quellnah, aber verlässlich. **Gold** ist für die Nutzung modelliert, typischerweise als dimensionales Modell für Business Intelligence.

**Warum diese Trennung sich lohnt:** Jede Schicht hat einen klaren Zweck und eine klare Zielgruppe. Bricht etwas, weiß man sofort, in welcher Schicht — Ingestion-Fehler in Bronze, Bereinigungs-Fehler in Silber, Modellierungs-Fehler in Gold. **Der Preis** ist, dass dieselben Daten mehrfach vorliegen (mehr Speicher, mehr Rechenzeit pro Lauf). Bei den Cloud-Preisen für Speicher ist das fast immer ein guter Tausch gegen die gewonnene Klarheit.

Wichtig ist, dass „Schicht" (Bronze/Silber/Gold) und „Technologie" (Lakehouse/Warehouse) zwei verschiedene Dinge sind. In diesem Projekt liegen Bronze und Silber im **Lakehouse** (flexibel, für Code/Spark), Gold im **Warehouse** (T-SQL, dimensional). Die Normalisierungs-Richtung dreht sich dabei bewusst um: Silber ist quellnah/normalisiert, Gold ist denormalisiert als Star-Schema — optimiert für schnelle Abfragen im Dashboard.

---

## 4. Was wurde hier konkret gebaut? — Der Gesamtüberblick

Öffentliche Verkaufsdaten eines brasilianischen Online-Marktplatzes wandern von einer Datei-Ablage in der Cloud durch die drei Schichten (Bronze, Silber, Gold) und enden in einem Dashboard und einem Vorhersage-Modell. Alles ist so organisiert, dass verschiedene „Abteilungen" ihre eigenen Bereiche besitzen.

![Gesamtarchitektur: Datenfluss von der Quelle über die Cloud-Ablage durch die Fabric-Plattform bis zu Dashboard und Machine Learning](docs/04-architecture.png)

Die Quelle liegt in **Azure Data Lake Storage Gen2** (nur die Rohdateien). Die Verarbeitung passiert komplett in **Microsoft Fabric** und ist über **GitHub** versioniert. Eine zentrale Plattform-Ebene übernimmt die Ingestion (Bronze); jede Fachdomäne baut daraus ihre Silber- und Gold-Produkte. Eine consumer-orientierte Data-Science-Domäne greift per Shortcut auf die Produkte zu.

Das Bewusste an diesem Design: Azure umschließt nur den Storage (die Rohdaten), nicht die ganze Plattform — die Grenze zwischen Azure-Storage und Fabric ist die Stelle, an der die Ingestion-Pipeline die Systemgrenze überquert. Git rahmt alles ab der Ingestion ein, weil genau dieser Teil versioniert wird. Rohdaten in Azure gehen bewusst nicht ins Git — Quelldaten gehören nicht in die Versionskontrolle des Codes, sie sind Input, nicht Artefakt.

---

## 5. Die Datenquelle

Echte (anonymisierte) Bestelldaten eines großen brasilianischen Online-Marktplatzes namens Olist — rund 100.000 Bestellungen mit Kunden, Produkten, Zahlungen, Bewertungen und Lieferzeiten.

Der [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) besteht aus neun CSV-Dateien, die über gemeinsame Schlüssel verknüpft sind (orders, order_items, customers, products, sellers, payments, reviews, geolocation, Kategorie-Übersetzung). Die relationale Struktur macht ihn ideal, um mehrere Domänen und ein echtes Star-Schema zu bauen.

**Zur Einordnung — was an dieser Quelle „zu schön" ist:** Der Datensatz ist bereits sauber, anonymisiert, einmalig exportiert und statisch. In einem echten Projekt kommen Daten laufend, unvollständig und uneinheitlich aus mehreren operativen Systemen (Shop, ERP, CRM, Zahlungsdienstleister) — oft mit widersprüchlichen Schlüsseln und ohne fertige Kategorie-Übersetzung. Vieles, was die Silber-Schicht hier in wenigen Zeilen erledigt, wäre dort ein eigenes, dauerhaftes Thema (Deduplizierung über Systemgrenzen, Schlüssel-Mapping, Nachladen verspäteter Sätze). Das ist der Grund, warum die folgende Struktur *robuster* wirkt, als der Datensatz sie streng genommen erfordert — sie ist so gebaut, dass sie den realen Fall aushalten würde.

---

## 6. Die Domänen — wer besitzt was

Die Plattform ist in fachliche Bereiche aufgeteilt, so wie ein Unternehmen Abteilungen hat. Eine **Domäne** bündelt Daten, Regeln und Verantwortung rund um einen klaren Teil des Geschäfts — zum Beispiel Verkauf, Zahlungen, Lieferungen oder Kundenkommunikation. Sie ist also keine technische Datenbank-Schublade, sondern eine **fachliche Grenze**: Das Team, das einen Bereich am besten versteht, verantwortet auch die Qualität und Bereitstellung seiner Daten.

Jede Domäne kann in kleinere **Subdomänen** zerlegt werden. Im Vertrieb sind das etwa Bestellabwicklung und Produktkatalog; in Finance sind es Zahlungen und Umsatz. Jede Subdomäne erhält einen eigenen Arbeitsraum (**Workspace**), in dem ihr Team Pipelines, Notebooks, Tabellen und Datenprodukte entwickelt und betreibt. Die Teams arbeiten damit selbstständig, folgen aber gemeinsamen Plattform- und Governance-Regeln.

![Domänen-Struktur: fachliche Bereiche mit Unterbereichen und Arbeitsräumen](docs/05-domains.png)

**Zwei Arten von Domänen — ein wichtiger Begriff:** Man unterscheidet, *woher* die Daten einer Domäne stammen.

- **Source-aligned** („an der Quelle ausgerichtet"): Die Domäne erzeugt Datenprodukte direkt aus ihrem eigenen fachlichen Verantwortungsbereich. Sie ist der Ursprung der Daten.
- **Consumer-aligned** („am Verbrauch ausgerichtet"): Die Domäne besitzt keine eigenen Quelldaten, sondern *nutzt* die veröffentlichten Produkte anderer Domänen, um daraus etwas Neues zu bauen.

In diesem Projekt gibt es vier *source-aligned* Domänen. Daneben steht **Data Science** als *consumer-aligned* Domäne: Sie besitzt nicht die Quelldaten, sondern konsumiert die Produkte anderer, um daraus Vorhersagen zu erstellen. Umgesetzt wird das mit **Fabric Domains** im Admin-Portal; jede Subdomäne ist ein eigener Workspace. Die Plattform-Ingestion gehört bewusst *keiner* Fachdomäne — sie ist geteilte Infrastruktur.

| Domäne | Subdomäne | Workspace |
|---|---|---|
| **Sales** | Order Management · Product & Catalog | `ws-sales-orders` · `ws-sales-catalog` |
| **Finance** | Payments · Revenue & Freight | `ws-finance-payments` · `ws-finance-revenue` |
| **Supply Chain** | Delivery · Seller Management | `ws-supply-delivery` · `ws-supply-sellers` |
| **Marketing & CX** | Customer · Reviews | `ws-mktg-customer` · `ws-mktg-reviews` |
| **Data Science** *(consumer)* | — | `ws-datascience` |

**Warum diese Aufteilung sinnvoll ist:** Ownership liegt näher an der Fachlichkeit. Das Sales-Team kann beispielsweise selbst entscheiden, wie ein verlässliches Umsatz-Datenprodukt aussehen muss, statt Anforderungen über mehrere Übergaben an ein zentrales Team zu schicken. Das verkürzt Wege, macht Verantwortung sichtbar und erlaubt, dass Domänen unabhängig weiterentwickelt werden. Zugleich können andere Teams veröffentlichte Datenprodukte per OneLake Shortcut nutzen, ohne Kopien anzulegen. So bleiben Daten auffindbar und wiederverwendbar, während ihre Herkunft klar bleibt.

**Die Kehrseite:** Mehr Autonomie bedeutet auch mehr Abstimmung. Ohne gemeinsame Namenskonventionen, Qualitätsregeln, Zugriffsrechte und klare Schnittstellen würden schnell widersprüchliche Kennzahlen oder isolierte Datensilos entstehen. Data Mesh verbindet daher dezentrale Verantwortung mit zentral vereinbarten Standards und Governance. Für ein kleines Projekt wäre eine vollständig getrennte Plattform oft überdimensioniert; hier bleibt die Bronze-Ingestion deshalb bewusst zentral, während die fachliche Verarbeitung ab Silber den Domänen gehört.

Jeder Workspace bindet an dasselbe Git-Repository, aber an einen eigenen Ordner (Mono-Repo mit `platform-ingestion/`, `domains/…`, `data-science/`). Datenprodukte werden zwischen Workspaces per OneLake Shortcut geteilt — das ist unabhängig von Git und passiert zur Laufzeit. Die Workspace-Grenze ist dabei eine organisatorische und berechtigungsrelevante Ownership-Grenze, nicht automatisch eine Kopie derselben Daten.

> **Ehrlich bleiben:** Data Mesh ist zuerst ein *organisatorisches* Modell — es lebt davon, dass echte, fachlich eigenständige Teams ihre Domänen betreiben. In diesem Portfolio spielt eine Person alle Rollen. Die Workspace- und Domänen-*Struktur* ist real umgesetzt; die dahinterstehende Team-Autonomie ist zwangsläufig simuliert. Das ändert nichts am gezeigten Architektur-Muster, sollte aber klar benannt sein.

---

## 7. Der Weg der Daten — Schritt für Schritt

### 7.1 Bronze: Daten hereinholen

Die Rohdateien werden aus der Cloud-Ablage unverändert in die Plattform kopiert — ein reiner Transport, bei dem noch nichts an den Daten geändert wird.

![Ingestion: eine Pipeline kopiert die Rohdateien in die Bronze-Schicht](docs/06-bronze-ingestion.png)

Eine **Data-Factory-Pipeline** (`pl_ingest_bronze`) kopiert alle neun CSVs per Copy-Aktivität unverändert (Format „Binary") in `lh_bronze/Files/bronze`. Bewusst roh gehalten, damit jede Bereinigung transparent im Code passiert und nicht schon beim Kopieren „unsichtbar" etwas verändert wird.

Der Zugriff der Domänen auf Bronze läuft danach nicht über Kopien, sondern über OneLake Shortcuts — eine zentrale Ingestion, viele Konsumenten. Geplant ist ein Ausbau zu einer metadata-driven ForEach-Pipeline, die über eine Dateiliste iteriert, statt neun fest verdrahteter Copy-Aktivitäten zu pflegen. In Produktion käme hier zusätzlich inkrementelles Laden ins Spiel (nur neue/geänderte Dateien), damit die Ingestion nicht mit jeder Datenmenge linear teurer wird.

### 7.2 Silber: Daten bereinigen

Die rohen Tabellen werden gesäubert — Datumsangaben werden zu echten Daten, Preise zu echten Zahlen, Duplikate fliegen raus.

Ein **PySpark-Notebook** (`nb_orders_silver`) liest die rohen CSVs (per Shortcut) und schreibt bereinigte **Delta-Tabellen**. Beispiel — der Kern der Transformation:

```python
from pyspark.sql.functions import col, to_timestamp
bronze = "Files/bronze"

df_orders = (
    spark.read.option("header", "true").csv(f"{bronze}/olist_orders_dataset.csv")
    .withColumn("order_purchase_timestamp", to_timestamp("order_purchase_timestamp"))
    .dropDuplicates(["order_id"])
)
df_orders.write.mode("overwrite").format("delta").saveAsTable("orders_silver")
```

Geldbeträge werden als `decimal(10,2)` typisiert (nicht `float` — vermeidet Rundungsfehler bei Geld), Produktkategorien werden von Portugiesisch nach Englisch gejoint. Silber bleibt bewusst quellnah (eine Tabelle je Entität), damit verschiedene Gold-Modelle darauf aufbauen können, ohne dass Silber schon eine bestimmte Auswertung vorwegnimmt. Das `overwrite` hier ist die Portfolio-Vereinfachung: Bei laufenden Quellen wäre es ein `MERGE`/Upsert (nur Änderungen einspielen) und idealerweise idempotent, damit ein erneuter Lauf keine Dubletten erzeugt.

### 7.3 Gold: Daten servierfertig modellieren

Aus den sauberen Tabellen wird ein Modell gebaut, das für Auswertungen optimiert ist — eine zentrale „Fakten"-Tabelle (was wurde verkauft, zu welchem Preis) umgeben von „Nachschlage"-Tabellen (welcher Kunde, welches Produkt, welches Datum).

![Star-Schema: eine zentrale Faktentabelle, umgeben von beschreibenden Dimensionstabellen](docs/07-star-schema.png)

Ein **Star-Schema** heißt so, weil in der Mitte die **Faktentabelle** steht (die messbaren Ereignisse — hier: verkaufte Artikel) und ringsum die **Dimensionstabellen** (der beschreibende Kontext — Kunde, Produkt, Datum). Aufgemalt ergibt das die Form eines Sterns. Dieses Modell ist der Klassiker für Business Intelligence, weil Abfragen wie „Umsatz pro Produktkategorie pro Monat" damit einfach und schnell werden.

Im **Warehouse** (`wh_orders_gold`) baut eine Stored Procedure per **T-SQL** ein dimensionales Kimball-Star-Schema. Die Faktentabelle liegt auf Positionsebene (eine Zeile pro bestelltem Artikel), umgeben von `dim_date`, `dim_customer`, `dim_product`, `dim_order`.

Der Build ist in einer Stored Procedure gekapselt und wird über eine **Pipeline** (`pl_build_gold_orders`) orchestriert — dadurch wiederholbar, planbar und in der Lineage (Datenherkunft) sichtbar. Der Zugriff aufs Silber-Lakehouse erfolgt per Cross-Database-Query, ohne die Daten zu kopieren. Die Faktentabelle auf Positionsebene (statt auf Bestellebene) ist bewusst gewählt: Sie ist die feinste sinnvolle Granularität und lässt sich später jederzeit zu Bestell- oder Monatsebene aggregieren — umgekehrt ginge es nicht.

---

## 8. Warum zwei verschiedene Datenbank-Typen? (Lakehouse vs. Warehouse)

Ein **Lakehouse** ist wie eine große, flexible Werkstatt — gut zum Verarbeiten, Experimentieren und für Code. Ein **Warehouse** ist wie ein aufgeräumter Ausstellungsraum — gut, um fertige Ergebnisse schnell und ordentlich zu präsentieren.

![Lakehouse vs. Warehouse: flexible Werkstatt gegenüber ordentlichem Ausstellungsraum](docs/08-lakehouse-vs-warehouse.png)

**Lakehouse** = offene Delta-/Parquet-Tabellen plus Spark; ideal für Engineering und Data Science, wo man in Code arbeitet und volle Flexibilität braucht. Man kann per SQL zwar lesen, aber nicht komfortabel schreiben. **Warehouse** = vollwertiges, auch *schreibendes* T-SQL; ideal als Serving-Schicht für BI-Konsumenten, die klassische SQL-Semantik (Stored Procedures, `INSERT`/`UPDATE`, Transaktionen) erwarten.

**Die Abwägung:**

- **Vorteil** des Nebeneinanders: jedes Werkzeug für das, was es am besten kann — Spark/Code für Transformation, T-SQL für kuratiertes Serving.
- **Der Preis dafür:** zwei Engines, zwei Betriebs- und Sicherheitsmodelle, Cross-Database-Queries und eine etwas kompliziertere Lineage.
- **Warum hier so:** Das Projekt will genau diese Wahl zeigen. Man *könnte* Gold auch im Lakehouse belassen und über dessen SQL-Endpunkt lesen — dann aber ohne schreibendes T-SQL und ohne den vertrauten Warehouse-Komfort für BI-Teams.

Die Zuordnung folgt der Medaillon-Schicht: Bronze/Silber im Lakehouse (Engineering), Gold im Warehouse (Serving). Genau dieses bewusste Nebeneinander — und die Fähigkeit zu begründen, *wann* welches Werkzeug passt — ist der Kern der Design-Kompetenz, die dieses Projekt zeigen soll. Nicht jede Domäne braucht beides: BI-lastige Domänen (Sales, Finance) bekommen ein Warehouse, verarbeitungslastige kommen mit dem Lakehouse aus.

---

## 9. Der Data-Science-Konsument: ein Datenprodukt nutzen

Ein „Data-Science-Team" nimmt die aufbereiteten Daten des Vertriebs — ohne sie zu kopieren — und baut daraus ein Modell, das die **Lieferzeit** neuer Bestellungen vorhersagt.

![Data Science als Konsument: greift per Shortcut auf die Daten zu und erzeugt ein eigenes Vorhersage-Produkt](docs/09-datascience.png)

Die Data-Science-Domäne greift per **OneLake Shortcut** auf die **Silber**-Tabellen von Sales zu (bewusst Silber statt Gold — Feature Engineering braucht die vollständigen, quellnahen Daten). Ein PySpark-/scikit-learn-Notebook baut eine Feature-Tabelle, trainiert ein **Random-Forest-Regressionsmodell** zur Vorhersage der Lieferzeit und schreibt das Ergebnis als eigenes Datenprodukt (`delivery_predictions`) in das DS-eigene Lakehouse zurück — nicht in die Quelldomäne. Das ist der entscheidende Punkt: Der Konsument verändert die Quelle nicht, sondern erzeugt ein *neues*, eigenes Produkt.

Die Trainingsläufe werden mit **MLflow** getrackt und sind in Fabric vergleichbar (Baseline vs. Iteration). Ergebnis der ersten Baseline: mittlerer Fehler von ~4,8 Tagen bei einer durchschnittlichen Lieferzeit von 12 Tagen. Wichtigster Treiber: die Region (Distanz zum Wirtschaftszentrum São Paulo) und die Frachtkosten. Eine Iteration mit dem Verkäufer-Standort brachte nur minimale Verbesserung (4,76 → 4,70 Tage) — lehrreich, weil die Frachtkosten die Distanz bereits abbilden (**Feature-Redundanz**: zwei Merkmale tragen dieselbe Information, das zweite bringt daher kaum Zusatznutzen). Der eigentliche Cross-Domain-Beweis ist hier zentral: *ein* Datenprodukt (Sales-Silber), konsumiert von einem anderen Team, das daraus ein neues Produkt macht — ohne Kopie, ohne die Quelle zu berühren, mit klar getrenntem Ownership.

---

## 10. Bewusste Design-Entscheidungen

Der wichtigste Teil für technisch versierte Leser — hier steckt das eigentliche „Warum". Jede Entscheidung hat einen Nutzen *und* einen Preis; interessant ist die Abwägung.

**Lakehouse für Engineering, Warehouse für Serving.**
Beide Engines nebeneinander, je nach Aufgabe (siehe Abschnitt 8). *Nutzen:* passendes Werkzeug je Schicht. *Preis:* zwei Engines und Cross-Database-Queries. *Warum:* zeigt bewusst die Werkzeugwahl statt eines Einheitsbreis.

**Zentrale Bronze-Ingestion statt einer pro Domäne.**
Eine Pipeline, eine Wahrheit für Rohdaten. *Nutzen:* keine mehrfach geladene Quelle, weniger Redundanz, einfacher Betrieb. *Preis:* die Ingestion ist geteilte Infrastruktur, die jemandem (einem Plattform-Team) gehören muss — eine Abweichung von der reinen Mesh-Lehre. *Warum:* bei einer Quelle ist das pragmatisch und vermeidet Overhead.

**Domänen-Trennung in Silber, nicht im Bronze-Shortcut.**
Der Shortcut verlinkt die gesamte Landing-Zone; die fachliche Trennung entsteht durch selektives Einlesen und später über Zugriffsrollen. *Nutzen:* eine einfache, zentrale Ingestion. *Preis:* die eigentliche Ownership-Grenze ist erst ab Silber hart. *Warum:* passt zum hybriden Ansatz aus Abschnitt 2.

**Modellierungstiefe nach Bedarf.**
Sales baut den Star direkt aus Silber (schlank). Für Finance ist bewusst eine normalisierte **3NF-Core-Schicht** vorgesehen — begründet durch Integrationsbedarf bei Wachstum (weitere Länder, weitere Quellsysteme). *Nutzen:* kein Overengineering dort, wo es nicht nötig ist. *Preis:* uneinheitliche Tiefe zwischen Domänen. **Data Vault 2.0** wurde bewertet und mangels wechselnder Quellen bewusst weggelassen — es glänzt bei vielen, sich ändernden Quellsystemen, die es hier schlicht nicht gibt.

**Slowly Changing Dimensions (SCD) als Type 1.**
Die Dimensionen sind Type 1 (überschreibend — der alte Wert wird ersetzt). *Nutzen:* einfach und klein. *Preis:* keine Historie; vergangene Zustände gehen verloren. *Warum:* Bei einem statischen Datensatz bringt Type-2-Historisierung (jede Änderung als neue Version aufbewahren) keinen Mehrwert. Bei sich ändernden Stammdaten — etwa Verkäufer, die den Standort wechseln — wäre Type 2 sinnvoll. Bewusst als Abwägung dokumentiert.

**Gold-Build als Stored Procedure + Pipeline** statt manuellem Skript.
*Nutzen:* wiederholbar, orchestrierbar, planbar, in der Lineage sichtbar. *Preis:* T-SQL-Logik ist schwerer testbar/portabel als Code, und die Cross-DB-Lineage bleibt lückenhaft (siehe unten). *Warum:* deutlich robuster als ein von Hand gestartetes Skript.

**Data Science konsumiert Silber, nicht Gold.**
Feature Engineering braucht rohere Daten als das für BI kuratierte, aggregierte Gold. *Nutzen:* volle Signalstärke fürs Modell. *Preis:* engere Kopplung ans Silber-Schema. *Warum:* ein Dashboard und ein Modell haben unterschiedliche Anforderungen an dieselben Daten.

**Bekannte Lineage-Grenze.**
T-SQL-Cross-Database-Transformationen werden in Fabric derzeit nicht spaltengenau bis in die Silber-Quelle verfolgt — eine dokumentierte Plattform-Einschränkung, kein Fehler im Design. Ehrlich zu benennen, wo das Werkzeug an eine Grenze stößt, gehört zur Architekturarbeit dazu.

---

## 11. Was in einem echten Projekt anders wäre

Ein Portfolio vereinfacht notwendigerweise. Diese Vereinfachungen offen zu benennen, ist selbst Teil der gezeigten Kompetenz — es zeigt, dass die Lücke zwischen Demo und Produktion bekannt ist. Die wichtigsten Punkte:

**Echte Teams statt einer Person.** Data Mesh ist zuerst ein Organisationsmodell. Produktiv betreiben fachlich eigenständige Teams ihre Domänen mit eigener Roadmap und Bereitschaft. Hier ist die *Struktur* real, die Team-Autonomie simuliert.

**Datenmenge und Skalierung.** 100.000 Bestellungen passen bequem in den Arbeitsspeicher. Echte Plattformen verarbeiten Millionen bis Milliarden Zeilen und brauchen dann Partitionierung, Liquid Clustering bzw. `OPTIMIZE`, inkrementelles Laden und **Kapazitätsplanung** (Fabric Capacity, F-SKUs). Vieles, was hier ein voller Overwrite ist, wäre dort ein inkrementeller Merge/Upsert oder CDC (Change Data Capture — nur die Änderungen).

**Eine Quelle statt vieler.** Ein einzelner, sauberer Datensatz. Der eigentliche Wert von Data Mesh und einer Integrationsschicht (3NF/Data Vault) zeigt sich erst bei vielen, uneinheitlichen Quellsystemen mit überlappenden Entitäten und widersprüchlichen Schlüsseln.

**Batch statt Echtzeit.** Alles läuft als geplanter Stapellauf (Batch). Echtzeit-Szenarien — Live-Bestelltracking, Betrugserkennung — würden **Real-Time Intelligence** (Eventstreams, KQL) ergänzen.

**Datenqualität als Framework.** Hier wird ad hoc im Notebook bereinigt. Produktiv gehören dazu deklarative Qualitätsregeln, automatisierte Tests, eine Quarantäne für fehlerhafte Sätze und **Data Contracts** — verbindliche Schema-Zusagen zwischen produzierender und konsumierender Domäne.

**Governance und Sicherheit.** In einem regulierten Umfeld wären Zugriffsrollen (OneLake Data Access Roles), Row-/Column-Level Security, Sensitivity Labels, ein Datenkatalog (**Microsoft Purview**) und durchgängige Lineage-Überwachung Pflicht. Hier nur teils skizziert und auf der Roadmap.

**Betrieb (Ops).** Zeitplanung, Monitoring, Alerting, Retry-Logik bei Fehlern, SLAs und Kostenüberwachung (FinOps) sind produktiv zentral. Hier bewusst minimal gehalten, damit die Architektur im Vordergrund steht.

**CI/CD und Umgebungen.** Produktiv trennt man **Dev → Test → Prod** über Deployment Pipelines, mit automatisierten Tests und Freigabeprozessen, statt direkt in einem Workspace zu arbeiten. Auch das steht auf der Roadmap, würde ein Portfolio aber überfrachten.

---

## 12. Tech-Stack

**Microsoft Fabric** (Lakehouse · Warehouse · Data Factory · Notebooks/PySpark · OneLake · OneLake Shortcuts · Domains · Git-Integration · MLflow · Semantic Model/Direct Lake) · **Azure Data Lake Storage Gen2** · **GitHub** (Mono-Repo) · **T-SQL** · **scikit-learn** · **Power BI** *(geplant)*

---

## 13. Aktueller Stand & Roadmap

| Bereich | Status |
|---|---|
| Azure-Setup (ADLS Gen2, Bronze-Container) | ✅ |
| Ingestion-Pipeline (ADLS → Bronze) | ✅ |
| Git-Integration (GitHub, Mono-Repo) | ✅ |
| Domänen & Subdomänen | ✅ Sales + Data Science |
| Silber (orders, order_items, customers, products, sellers) | ✅ |
| Gold — Star-Schema (Stored Proc + Pipeline) | ✅ |
| Data Science — Modell + MLflow + Datenprodukt | ✅ Baseline + Iteration |
| Semantic Model (Direct Lake) + Power-BI-Dashboard | ⏳ geplant |

**Geplante Erweiterungen**

- **ML v3:** echte geografische Distanz (Haversine) als Feature statt nur Bundesstaat/Fracht
- Semantic Model (Direct Lake) + Power-BI-Dashboard (Prognose vs. Realität, Umsatz nach Kategorie/Region, Lieferzeiten)
- Metadata-driven ForEach-Pipeline; inkrementelles Laden als CDC-Ersatz
- Robustheit: Fehlerverzweigung, Lauf-Logging, Parametrisierung
- Governance: OneLake Data Access Roles, Row-/Column-Level Security
- Finance-Domäne mit normalisiertem 3NF-Core; `sellers` domänenrichtig in Supply Chain
- Restliche Domänen · Deployment Pipelines (Dev → Test → Prod) · Data Activator

---

<sub>Portfolio-Projekt. Aufbau und Design-Entscheidungen sind bewusst dokumentiert, um Architektur-Kompetenz im Microsoft-Fabric-Stack zu zeigen — nicht als produktionsfertige Plattform, sondern als nachvollziehbares Referenzbeispiel.</sub>
