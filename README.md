# E-Commerce-Datenplattform auf Microsoft Fabric

**Data Mesh & Medaillon-Architektur — von Rohdaten zu Dashboards und Machine Learning.**

<sub>Repository: `fabric-ecommerce-datamesh`</sub>

Dieses Projekt nimmt öffentliche E-Commerce-Daten und verwandelt sie Schritt für Schritt in aufbereitete Kennzahlen, Dashboards und ein Machine-Learning-Modell — organisiert nach den Prinzipien **Data Mesh** und **Medaillon-Architektur**. Es ist ein Portfolio-Projekt, das zeigen soll, *wie* man Datenplattformen strukturiert und *warum* man bestimmte Entscheidungen trifft.

> 📖 **Wie man dieses README liest:** Jeder Abschnitt beginnt einfach und für alle verständlich und wird dann Stück für Stück technischer. Wer nur einen Überblick will, liest die ersten Absätze jedes Abschnitts. Wer tiefer einsteigen möchte, findet darunter Details, Code und Design-Entscheidungen.

---

## 1. Das Problem: Warum überhaupt eine besondere Architektur?

**Ganz einfach gesagt:** In vielen Unternehmen gibt es *ein* zentrales Datenteam. Jede Abteilung — Vertrieb, Marketing, Finanzen, Logistik — muss bei diesem einen Team anfragen, wenn sie eine Auswertung, ein Dashboard oder einen neuen Datensatz braucht. Das Team wird zum **Bottleneck**: Anfragen stapeln sich, alle warten, und die Abteilungen, die ihre eigenen Daten am besten kennen, dürfen nicht selbst ran.

![Der Bottleneck: ein zentrales Datenteam bremst alle Abteilungen aus](docs/01-bottleneck.png)

Dieser zentralistische Ansatz skaliert schlecht. Das zentrale Team versteht die Fachlichkeit einzelner Bereiche nie so gut wie die Bereiche selbst, Wissen geht in der Übergabe verloren, und mit jeder neuen Abteilung wächst der Rückstau. Genau hier setzt **Data Mesh** an.

---

## 2. Was ist Data Mesh?

**Ganz einfach gesagt:** Statt einer zentralen Datenküche, die für alle kocht, bekommt **jede Abteilung ihre eigene kleine Küche** — betreibt sie aber nach gemeinsamen Standards. Jede Abteilung ist für ihre eigenen Daten verantwortlich und stellt sie den anderen als fertiges, verlässliches **„Datenprodukt"** zur Verfügung — so wie ein Team im Supermarkt ein fertig verpacktes Produkt ins Regal stellt, das andere einfach nehmen können.

![Zentralisiert vs. Data Mesh: von einem Team für alle zu Datenprodukten pro Domäne](docs/02-centralized-vs-mesh.png)

Data Mesh beruht auf vier Prinzipien: (1) **Domain Ownership** — fachliche Bereiche besitzen ihre Daten; (2) **Data as a Product** — Daten werden wie ein Produkt gepflegt und bereitgestellt; (3) **Self-Serve-Plattform** — eine gemeinsame technische Basis, auf der alle bauen; (4) **föderierte Governance** — gemeinsame Regeln, aber dezentrale Umsetzung.

**Für Fortgeschrittene:** In Microsoft Fabric bilde ich diese Prinzipien konkret ab über **Fabric Domains** (fachliche Gruppierung), **einen Workspace pro Subdomäne** (Ownership-Grenze) und **OneLake Shortcuts** (Datenprodukte werden ohne Kopie geteilt — „zero-copy"). Die Self-Serve-Plattform ist Fabric selbst; die Governance regeln später Zugriffsrollen. Wichtig: Ich baue bewusst einen **hybriden** Ansatz — eine geteilte zentrale Ingestion für Rohdaten, aber domänen-eigene Verarbeitung. Das vermeidet, dass jede Domäne dieselbe Quelle mehrfach lädt, und hält trotzdem das Ownership dort, wo es zählt.

---

## 3. Die Medaillon-Architektur: Bronze, Silber, Gold

**Ganz einfach gesagt:** Rohdaten sind wie frisch eingekaufte Zutaten — man kann sie nicht direkt servieren. Deshalb durchlaufen die Daten drei Stufen, wie in einer Küche:

- 🥉 **Bronze** = die rohen Zutaten, so wie sie ankommen (unverändert, ungewaschen).
- 🥈 **Silber** = gewaschen, geschnitten, sortiert (bereinigt und in eine saubere Form gebracht).
- 🥇 **Gold** = das fertige Gericht, angerichtet und servierfertig (aufbereitet für Auswertungen und Dashboards).

![Medaillon-Architektur: von rohen Daten über bereinigte bis zu servierfertigen Daten](docs/03-medallion.png)

Die drei Schichten trennen Verantwortlichkeiten. Bronze bewahrt die Rohdaten unverändert (Nachvollziehbarkeit, Wiederholbarkeit). Silber enthält bereinigte, typisierte Tabellen — eine pro Quell-Entität, quellnah, aber verlässlich. Gold ist für die Nutzung modelliert, typischerweise als dimensionales Modell für Business Intelligence.

**Für Fortgeschrittene:** Wichtig ist, dass „Schicht" (Bronze/Silber/Gold) und „Technologie" (Lakehouse/Warehouse) zwei verschiedene Dinge sind. In diesem Projekt liegen Bronze und Silber im **Lakehouse** (flexibel, für Code/Spark), Gold im **Warehouse** (T-SQL, dimensional). Die Normalisierungs-Richtung dreht sich dabei bewusst um: Silber ist quellnah/normalisiert, Gold ist denormalisiert als Star-Schema — optimiert für schnelle Abfragen im Dashboard.

---

## 4. Was wurde hier konkret gebaut? — Der Gesamtüberblick

**Ganz einfach gesagt:** Öffentliche Verkaufsdaten eines brasilianischen Online-Marktplatzes wandern von einer Datei-Ablage in der Cloud durch die drei Küchen-Stufen und enden in einem Dashboard und einem Vorhersage-Modell. Alles ist so organisiert, dass verschiedene „Abteilungen" ihre eigenen Bereiche besitzen.

![Gesamtarchitektur: Datenfluss von der Quelle über die Cloud-Ablage durch die Fabric-Plattform bis zu Dashboard und Machine Learning](docs/04-architecture.png)

Die Quelle liegt in **Azure Data Lake Storage Gen2** (nur die Rohdateien). Die Verarbeitung passiert komplett in **Microsoft Fabric** und ist über **GitHub** versioniert. Eine zentrale Plattform-Ebene übernimmt die Ingestion (Bronze); jede Fachdomäne baut daraus ihre Silber- und Gold-Produkte. Eine consumer-orientierte Data-Science-Domäne greift per Shortcut auf die Produkte zu.

**Für Fortgeschrittene:** Das Bewusste an diesem Design: Azure umschließt nur den Storage (die Rohdaten), nicht die ganze Plattform — die Grenze zwischen Azure-Storage und Fabric ist die Stelle, an der die Ingestion-Pipeline die Systemgrenze überquert. Git rahmt alles ab der Ingestion ein, weil genau dieser Teil versioniert wird. Rohdaten in Azure gehen bewusst nicht ins Git.

---

## 5. Die Datenquelle

**Ganz einfach gesagt:** Echte (anonymisierte) Bestelldaten eines großen brasilianischen Online-Marktplatzes namens Olist — rund 100.000 Bestellungen mit Kunden, Produkten, Zahlungen, Bewertungen und Lieferzeiten.

Der [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) besteht aus neun CSV-Dateien, die über gemeinsame Schlüssel verknüpft sind (orders, order_items, customers, products, sellers, payments, reviews, geolocation, Kategorie-Übersetzung). Die relationale Struktur macht ihn ideal, um mehrere Domänen und ein echtes Star-Schema zu bauen.

---

## 6. Die Domänen — wer besitzt was

**Ganz einfach gesagt:** Die Plattform ist in fachliche Bereiche aufgeteilt, so wie ein Unternehmen Abteilungen hat. Jeder Bereich („Domäne") hat Unterbereiche („Subdomänen"), und jeder Unterbereich hat seinen eigenen Arbeitsraum.

![Domänen-Struktur: fachliche Bereiche mit Unterbereichen und Arbeitsräumen](docs/05-domains.png)

Vier *source-aligned* Domänen (die Daten erzeugen) und eine *consumer-aligned* Domäne (Data Science, die Daten nutzt). Umgesetzt als **Fabric Domains** im Admin-Portal; jede Subdomäne ist ein eigener Workspace. Die Plattform-Ingestion gehört bewusst *keiner* Fachdomäne — sie ist geteilte Infrastruktur.

| Domäne | Subdomäne | Workspace |
|---|---|---|
| **Sales** | Order Management · Product & Catalog | `ws-sales-orders` · `ws-sales-catalog` |
| **Finance** | Payments · Revenue & Freight | `ws-finance-payments` · `ws-finance-revenue` |
| **Supply Chain** | Delivery · Seller Management | `ws-supply-delivery` · `ws-supply-sellers` |
| **Marketing & CX** | Customer · Reviews | `ws-mktg-customer` · `ws-mktg-reviews` |
| **Data Science** *(consumer)* | — | `ws-datascience` |

**Für Fortgeschrittene:** Jeder Workspace bindet an dasselbe Git-Repository, aber an einen eigenen Ordner (Mono-Repo mit `platform-ingestion/`, `domains/…`, `data-science/`). Datenprodukte werden zwischen Workspaces per OneLake Shortcut geteilt — das ist unabhängig von Git und passiert zur Laufzeit.

---

## 7. Der Weg der Daten — Schritt für Schritt

### 7.1 Bronze: Daten hereinholen

**Ganz einfach gesagt:** Die Rohdateien werden aus der Cloud-Ablage unverändert in die Plattform kopiert — wie das Ausladen der Einkäufe in die Küche.

![Ingestion: eine Pipeline kopiert die Rohdateien in die Bronze-Schicht](docs/06-bronze-ingestion.png)

Eine **Data-Factory-Pipeline** (`pl_ingest_bronze`) kopiert alle neun CSVs per Copy-Aktivität unverändert (Format „Binary") in `lh_bronze/Files/bronze`. Bewusst roh gehalten, damit jede Bereinigung transparent im Code passiert.

**Für Fortgeschrittene:** Der Zugriff der Domänen auf Bronze läuft danach nicht über Kopien, sondern über OneLake Shortcuts — eine zentrale Ingestion, viele Konsumenten. Geplant ist ein Ausbau zu einer metadata-driven ForEach-Pipeline, die über eine Dateiliste iteriert.

### 7.2 Silber: Daten bereinigen

**Ganz einfach gesagt:** Die rohen Tabellen werden gesäubert — Datumsangaben werden zu echten Daten, Preise zu echten Zahlen, Duplikate fliegen raus.

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

**Für Fortgeschrittene:** Geldbeträge werden als `decimal(10,2)` typisiert (nicht Float — vermeidet Rundungsfehler), Produktkategorien werden von Portugiesisch nach Englisch gejoint. Silber bleibt bewusst quellnah (eine Tabelle je Entität), damit verschiedene Gold-Modelle darauf aufbauen können.

### 7.3 Gold: Daten servierfertig modellieren

**Ganz einfach gesagt:** Aus den sauberen Tabellen wird ein Modell gebaut, das für Auswertungen optimiert ist — eine zentrale „Fakten"-Tabelle (was wurde verkauft, zu welchem Preis) umgeben von „Nachschlage"-Tabellen (welcher Kunde, welches Produkt, welches Datum).

![Star-Schema: eine zentrale Faktentabelle, umgeben von beschreibenden Dimensionstabellen](docs/07-star-schema.png)

Im **Warehouse** (`wh_orders_gold`) baut eine Stored Procedure per **T-SQL** ein dimensionales Kimball-Star-Schema. Die Faktentabelle liegt auf Positionsebene (eine Zeile pro bestelltem Artikel), umgeben von `dim_date`, `dim_customer`, `dim_product`, `dim_order`.

**Für Fortgeschrittene:** Der Build ist in einer Stored Procedure gekapselt und wird über eine **Pipeline** (`pl_build_gold_orders`) orchestriert — dadurch wiederholbar, planbar und in der Lineage sichtbar. Der Zugriff aufs Silber-Lakehouse erfolgt per Cross-Database-Query, ohne die Daten zu kopieren.

---

## 8. Warum zwei verschiedene Datenbank-Typen? (Lakehouse vs. Warehouse)

**Ganz einfach gesagt:** Ein **Lakehouse** ist wie eine große, flexible Werkstatt — gut zum Verarbeiten, Experimentieren und für Code. Ein **Warehouse** ist wie ein aufgeräumter Ausstellungsraum — gut, um fertige Ergebnisse schnell und ordentlich zu präsentieren.

![Lakehouse vs. Warehouse: flexible Werkstatt gegenüber ordentlichem Ausstellungsraum](docs/08-lakehouse-vs-warehouse.png)

Lakehouse = offene Delta-/Parquet-Tabellen plus Spark; ideal für Engineering und Data Science. Warehouse = vollwertiges, schreibendes T-SQL; ideal als Serving-Schicht für BI-Konsumenten, die klassische SQL-Semantik erwarten.

**Für Fortgeschrittene:** Die Zuordnung folgt der Medaillon-Schicht: Bronze/Silber im Lakehouse (Engineering), Gold im Warehouse (Serving). Genau dieses bewusste Nebeneinander — und die Fähigkeit zu begründen, *wann* welches Werkzeug passt — ist der Kern der Design-Kompetenz, die dieses Projekt zeigen soll. Nicht jede Domäne braucht beides: BI-lastige Domänen (Sales, Finance) bekommen ein Warehouse, verarbeitungslastige kommen mit dem Lakehouse aus.

---

## 9. Der Data-Science-Konsument: ein Datenprodukt nutzen

**Ganz einfach gesagt:** Ein „Data-Science-Team" nimmt die aufbereiteten Daten des Vertriebs — ohne sie zu kopieren — und baut daraus ein Modell, das die **Lieferzeit** neuer Bestellungen vorhersagt.

![Data Science als Konsument: greift per Shortcut auf die Daten zu und erzeugt ein eigenes Vorhersage-Produkt](docs/09-datascience.png)

Die Data-Science-Domäne greift per **OneLake Shortcut** auf die **Silber**-Tabellen von Sales zu (bewusst Silber statt Gold — Feature Engineering braucht die vollständigen, quellnahen Daten). Ein PySpark-/scikit-learn-Notebook baut eine Feature-Tabelle, trainiert ein **Random-Forest-Regressionsmodell** zur Vorhersage der Lieferzeit und schreibt das Ergebnis als eigenes Datenprodukt (`delivery_predictions`) in das DS-eigene Lakehouse zurück — nicht in die Quelldomäne.

**Für Fortgeschrittene:** Die Trainingsläufe werden mit **MLflow** getrackt und sind in Fabric vergleichbar (Baseline vs. Iteration). Ergebnis der ersten Baseline: mittlerer Fehler von ~4,8 Tagen bei einer durchschnittlichen Lieferzeit von 12 Tagen. Wichtigster Treiber: die Region (Distanz zum Wirtschaftszentrum São Paulo) und die Frachtkosten. Eine Iteration mit dem Verkäufer-Standort brachte nur minimale Verbesserung (4,76 → 4,70 Tage) — lehrreich, weil die Frachtkosten die Distanz bereits abbilden (**Feature-Redundanz**). Der eigentliche Cross-Domain-Beweis ist hier zentral: *ein* Datenprodukt (Sales-Silber), konsumiert von einem anderen Team, das daraus ein neues Produkt macht.

---

## 10. Bewusste Design-Entscheidungen

Der wichtigste Teil für technisch versierte Leser — hier steckt das eigentliche „Warum":

- **Lakehouse für Engineering, Warehouse für Serving.** Beide Engines nebeneinander, je nach Aufgabe.
- **Zentrale Bronze-Ingestion statt pro Domäne.** Eine Pipeline, eine Wahrheit für Rohdaten; löst mehrfach genutzte Quelltabellen ohne Duplikate.
- **Domänen-Trennung in Silber, nicht im Bronze-Shortcut.** Der Shortcut verlinkt die gesamte Landing-Zone; die Trennung entsteht durch selektives Einlesen und später über Zugriffsrollen.
- **Modellierungstiefe nach Bedarf.** Sales baut den Star direkt aus Silber (schlank). Für Finance ist bewusst eine normalisierte 3NF-Core-Schicht vorgesehen — begründet durch Integrationsbedarf bei Wachstum (weitere Länder, weitere Quellsysteme). **Data Vault 2.0** wurde bewertet und mangels wechselnder Quellen bewusst weggelassen.
- **Slowly Changing Dimensions (SCD).** Die Dimensionen sind Type 1 (überschreibend). Bei einem statischen Datensatz bringt Type-2-Historisierung keinen Mehrwert; bei sich ändernden Stammdaten (z. B. Verkäufer, die den Standort wechseln) wäre sie sinnvoll — bewusst als Design-Abwägung dokumentiert.
- **Gold-Build als Stored Procedure + Pipeline** statt manuellem Skript: wiederholbar, orchestrierbar, planbar.
- **Data Science konsumiert Silber, nicht Gold.** Feature Engineering braucht rohere Daten als das für BI kuratierte Gold.
- **Bekannte Lineage-Grenze.** T-SQL-Cross-Database-Transformationen werden nicht spaltengenau bis in die Silber-Quelle verfolgt — eine dokumentierte Fabric-Einschränkung, kein Fehler.

---

## 11. Tech-Stack

**Microsoft Fabric** (Lakehouse · Warehouse · Data Factory · Notebooks/PySpark · OneLake Shortcuts · Domains · Git-Integration · MLflow) · **Azure Data Lake Storage Gen2** · **GitHub** (Mono-Repo) · **T-SQL** · **scikit-learn** · **Power BI** *(geplant)*

---

## 12. Aktueller Stand & Roadmap

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

