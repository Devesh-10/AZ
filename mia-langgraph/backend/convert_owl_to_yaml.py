"""
Convert MIA OWL ontology (.ttl) to a complete YAML representation.
Preserves all classes, object properties, data properties, individuals,
domains, ranges, subclass/subproperty hierarchies, and reference data.
"""

import yaml
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD
from rdflib.namespace import SKOS, DCTERMS
from collections import defaultdict

# Load ontology
g = Graph()
g.parse("/Users/devesh.b.sharma/Downloads/manufacturing-insight-agent-ao.ttl", format="turtle")

# Namespaces
MIA = Namespace("https://pid.astrazeneca.net/ontology/app/mia/")
DEF_OPS = Namespace("https://pid.astrazeneca.net/def-ops/")
REF_OPS = Namespace("https://pid.astrazeneca.net/ref-ops/")

g.bind("mia", MIA)
g.bind("def-ops", DEF_OPS)
g.bind("ref-ops", REF_OPS)


def short_name(uri):
    """Convert full URI to short readable name."""
    uri_str = str(uri)
    for prefix, ns in [("mia:", str(MIA)), ("def-ops:", str(DEF_OPS)),
                        ("ref-ops:", str(REF_OPS)), ("skos:", str(SKOS)),
                        ("owl:", str(OWL)), ("rdfs:", str(RDFS)),
                        ("xsd:", str(XSD)), ("rdf:", str(RDF)),
                        ("dcterms:", str(DCTERMS))]:
        if uri_str.startswith(ns):
            return prefix + uri_str[len(ns):]
    return uri_str


def get_label(subject):
    """Get rdfs:label for a subject."""
    for o in g.objects(subject, RDFS.label):
        return str(o)
    return None


def get_comment(subject):
    """Get rdfs:comment for a subject."""
    for o in g.objects(subject, RDFS.comment):
        return str(o)
    return None


def get_references(subject):
    """Get dcterms:references for a subject."""
    for o in g.objects(subject, DCTERMS.references):
        return str(o)
    return None


def resolve_domain_range(subject, predicate):
    """Resolve domain/range, handling owl:unionOf."""
    results = []
    for obj in g.objects(subject, predicate):
        # Check if it's a union (blank node with owl:unionOf)
        union_list = list(g.objects(obj, OWL.unionOf))
        if union_list:
            # Walk the RDF list
            items = []
            node = union_list[0]
            while node and str(node) != str(RDF.nil):
                first = list(g.objects(node, RDF.first))
                rest = list(g.objects(node, RDF.rest))
                if first:
                    items.append(short_name(first[0]))
                node = rest[0] if rest else None
            results.extend(items)
        else:
            results.append(short_name(obj))
    return results


# ========== ONTOLOGY METADATA ==========
ontology_meta = {}
ont_uri = MIA[""]  # The ontology URI itself
# Try the full URI too
for s in g.subjects(RDF.type, OWL.Ontology):
    for p, o in g.predicate_objects(s):
        pname = short_name(p)
        if pname in ("rdf:type",):
            continue
        key = pname.replace("dcterms:", "").replace("rdfs:", "").replace("owl:", "").replace("skos:", "")
        ontology_meta[key] = str(o)

# ========== CLASSES ==========
classes = {}
# Skip built-in OWL/SKOS classes
SKIP_CLASSES = {str(OWL.Thing), str(OWL.Nothing), str(SKOS.Concept), str(SKOS.ConceptScheme)}

for cls in g.subjects(RDF.type, OWL.Class):
    uri_str = str(cls)
    if uri_str in SKIP_CLASSES:
        # Still include skos:Concept and skos:ConceptScheme as they're used in the ontology
        pass

    name = short_name(cls)
    if name.startswith("owl:") or name.startswith("rdf:") or name.startswith("rdfs:"):
        continue

    # Skip blank nodes (anonymous classes from owl:unionOf restrictions)
    from rdflib import BNode
    if isinstance(cls, BNode):
        continue

    entry = {"uri": uri_str}

    label = get_label(cls)
    if label:
        entry["label"] = label

    comment = get_comment(cls)
    if comment:
        entry["description"] = comment

    refs = get_references(cls)
    if refs:
        entry["references"] = refs

    # Subclass
    for parent in g.objects(cls, RDFS.subClassOf):
        # Skip blank nodes (restrictions)
        if isinstance(parent, BNode):
            continue
        parent_name = short_name(parent)
        entry["subClassOf"] = parent_name

    classes[name] = entry

# Also add skos:Concept and skos:ConceptScheme since they're declared
classes["skos:Concept"] = {"uri": str(SKOS.Concept), "label": "Concept"}
classes["skos:ConceptScheme"] = {"uri": str(SKOS.ConceptScheme), "label": "Concept Scheme"}

# ========== OBJECT PROPERTIES ==========
object_properties = {}
SKIP_PROPS = {str(OWL.topObjectProperty)}

for prop in g.subjects(RDF.type, OWL.ObjectProperty):
    uri_str = str(prop)
    if uri_str in SKIP_PROPS:
        continue

    name = short_name(prop)
    if name.startswith("owl:"):
        continue

    entry = {"uri": uri_str}

    label = get_label(prop)
    if label:
        entry["label"] = label

    comment = get_comment(prop)
    if comment:
        entry["description"] = comment

    refs = get_references(prop)
    if refs:
        entry["references"] = refs

    # SubPropertyOf
    for parent in g.objects(prop, RDFS.subPropertyOf):
        parent_name = short_name(parent)
        if not parent_name.startswith("owl:"):
            entry["subPropertyOf"] = parent_name

    # Domain (with union support)
    domains = resolve_domain_range(prop, RDFS.domain)
    if len(domains) == 1:
        entry["domain"] = domains[0]
    elif len(domains) > 1:
        entry["domain"] = domains

    # Range (with union support)
    ranges = resolve_domain_range(prop, RDFS.range)
    if len(ranges) == 1:
        entry["range"] = ranges[0]
    elif len(ranges) > 1:
        entry["range"] = ranges

    object_properties[name] = entry

# ========== DATA PROPERTIES ==========
data_properties = {}
SKIP_DATA_PROPS = {str(OWL.topDataProperty)}

for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
    uri_str = str(prop)
    if uri_str in SKIP_DATA_PROPS:
        continue

    name = short_name(prop)
    if name.startswith("owl:"):
        continue

    entry = {"uri": uri_str}

    label = get_label(prop)
    if label:
        entry["label"] = label

    comment = get_comment(prop)
    if comment:
        entry["description"] = comment

    # SubPropertyOf
    for parent in g.objects(prop, RDFS.subPropertyOf):
        parent_name = short_name(parent)
        if not parent_name.startswith("owl:"):
            entry["subPropertyOf"] = parent_name

    # Domain (with union support)
    domains = resolve_domain_range(prop, RDFS.domain)
    if len(domains) == 1:
        entry["domain"] = domains[0]
    elif len(domains) > 1:
        entry["domain"] = domains

    # Range
    ranges = resolve_domain_range(prop, RDFS.range)
    if len(ranges) == 1:
        entry["range"] = ranges[0]
    elif len(ranges) > 1:
        entry["range"] = ranges

    data_properties[name] = entry

# ========== INDIVIDUALS (Reference Data) ==========
# Group by ConceptScheme
concept_schemes = {}
standalone_individuals = {}

for ind in g.subjects(RDF.type, OWL.NamedIndividual):
    name = short_name(ind)
    uri_str = str(ind)

    # Check if it's a ConceptScheme
    if (ind, RDF.type, SKOS.ConceptScheme) in g:
        scheme_entry = {
            "uri": uri_str,
            "label": get_label(ind) or name,
            "type": "skos:ConceptScheme",
            "concepts": []
        }
        # Get definition
        for o in g.objects(ind, SKOS.definition):
            scheme_entry["definition"] = str(o)
        concept_schemes[name] = scheme_entry

    elif (ind, RDF.type, SKOS.Concept) in g:
        # Find which scheme this belongs to
        for scheme_uri in g.objects(ind, SKOS.inScheme):
            scheme_name = short_name(scheme_uri)
            concept_entry = {
                "uri": uri_str,
                "label": get_label(ind) or name
            }
            for o in g.objects(ind, SKOS.prefLabel):
                concept_entry["prefLabel"] = str(o)

            # Will attach to scheme after all are collected
            if scheme_name not in concept_schemes:
                concept_schemes[scheme_name] = {
                    "uri": str(scheme_uri),
                    "label": scheme_name,
                    "type": "skos:ConceptScheme",
                    "concepts": []
                }
            concept_schemes[scheme_name]["concepts"].append({
                "id": name,
                **concept_entry
            })
    else:
        standalone_individuals[name] = {
            "uri": uri_str,
            "label": get_label(ind) or name
        }

# ========== ANNOTATION PROPERTIES ==========
annotation_properties = []
for prop in g.subjects(RDF.type, OWL.AnnotationProperty):
    name = short_name(prop)
    if not name.startswith("owl:") and not name.startswith("rdf:"):
        annotation_properties.append(name)

# ========== DATATYPES ==========
datatypes = []
for dt in g.subjects(RDF.type, RDFS.Datatype):
    datatypes.append(short_name(dt))

# ========== BUILD FINAL YAML ==========
ontology_yaml = {
    "ontology": {
        "metadata": ontology_meta,
        "prefixes": {
            "mia": str(MIA),
            "def-ops": str(DEF_OPS),
            "ref-ops": str(REF_OPS),
            "skos": str(SKOS),
            "owl": str(OWL),
            "rdfs": str(RDFS),
            "xsd": str(XSD),
            "dcterms": str(DCTERMS),
        },
        "datatypes": sorted(datatypes),
        "annotation_properties": sorted(annotation_properties),
        "classes": dict(sorted(classes.items())),
        "object_properties": dict(sorted(object_properties.items())),
        "data_properties": dict(sorted(data_properties.items())),
        "reference_data": dict(sorted(concept_schemes.items())),
    }
}

# Write YAML
output_path = "/Users/devesh.b.sharma/Astra Zeneca/mia-langgraph/backend/app/ontology/manufacturing-insight-agent-ontology.yaml"

# Ensure directory exists
import os
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Custom representer to handle long strings nicely
def str_representer(dumper, data):
    if '\n' in data or len(data) > 120:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_representer)

with open(output_path, "w") as f:
    yaml.dump(ontology_yaml, f, default_flow_style=False, sort_keys=False, width=120, allow_unicode=True)

# Print summary
print(f"✓ YAML written to: {output_path}")
print(f"  Classes: {len(classes)}")
print(f"  Object Properties: {len(object_properties)}")
print(f"  Data Properties: {len(data_properties)}")
print(f"  Reference Data Schemes: {len(concept_schemes)}")
total_concepts = sum(len(s.get('concepts', [])) for s in concept_schemes.values())
print(f"  Reference Data Concepts: {total_concepts}")
print(f"  Annotation Properties: {len(annotation_properties)}")
print(f"  Datatypes: {len(datatypes)}")
