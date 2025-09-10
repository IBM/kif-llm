import { http, HttpResponse } from 'msw';
import { QueryResponse, Statement } from 'model/Wikidata';

const API_URL = import.meta.env.VITE_API_BASE_URL;


const mockStatements: Statement[] = [
    {
        subject: {
            iri: 'https://www.wikidata.org/wiki/Q5950',
            label: 'James Brown',
            description: ''
        },
        snak: {
            property: {
                label: 'place of birth',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            },
            value: {
                label: 'Barnwell',
                iri: 'https://www.wikidata.org/wiki/Q586262',
                description: ''
            }
        },
        // qualifiers: [
        //     {
        //         property: {
        //             label: 'subject has role',
        //             iri: 'https://www.wikidata.org/wiki/Property:P2868'
        //         },
        //         value: {
        //             label: 'researcher',
        //             iri: 'https://www.wikidata.org/wiki/Q1650915'
        //         }
        //     },
        // ],
        // references: [
        //     {
        //         property: {
        //             label: 'reference URL',
        //             iri: 'https://www.wikidata.org/wiki/Property:P854'
        //         },
        //         value: {
        //             label: 'Test',
        //             iri: 'https://www.wikidata.org/wiki/Q1650915'
        //         }
        //     },
        // ]
    },
    {
        subject: {
            iri: 'https://www.wikidata.org/wiki/Q5950',
            label: 'James Brown',
            description: ''
        },
        snak: {
            property: {
                label: 'place of birth',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            },
            value: {
                label: 'Augusta',
                iri: 'https://www.wikidata.org/wiki/Q181962',
                description: ''
            }
        }
    },
    {
        subject: {
            iri: 'https://www.wikidata.org/wiki/Q6130347',
            label: 'James Brown',
            description: ''
        },
        snak: {
            property: {
                label: 'place of birth',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            },
            value: {
                label: 'Washington, D.C.',
                iri: 'https://www.wikidata.org/wiki/Q61',
                description: ''
            }
        },
    },
    {
        subject: {
            iri: 'https://dbpedia.org/page/James_Brown',
            label: 'James Brown',
            description: ''
        },
        snak: {
            property: {
                label: 'birthPlace',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            },
            value: {
                label: 'Barnwell, South Carolina',
                iri: 'https://dbpedia.org/page/Barnwell,_South_Carolina',
                description: ''

            }
        },
    }
];

const mockStatementsUsage: Statement[] = [
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
            label: 'Benzene',
            description: 'Benzene is an organic chemical compound with the molecular formula C6H6...'
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Fragrance',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/61',
                description: ''
            }
        },
    },
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
            label: 'Benzene',
            description: 'Benzene is an organic chemical compound with the molecular formula C6H6...'
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Propellants, non-motive (blowing agents)',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/90',
                description: ''
            }
        },
    },
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3020596',
            label: 'Ethylbenzene',
            description: ''
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Adhesion/cohesion promoter',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/3',
                description: ''
            }
        },
    },
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3020596',
            label: 'Ethylbenzene',
            description: ''
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Solvent',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/100',
                description: ''
            }
        },
    },
];

const queryResponse: QueryResponse = {
    statements: mockStatements,
    pattern: [{
        subject: "James Brown",
        predicate: "place of birth",
        object: "?x"}],
    mainEntity: "James Brown",
    items: [{
        iri: 'https://www.wikidata.org/wiki/Q5950',
        label: 'James Brown',
        description: 'American musician (1933–2006)'
    },
    {
        iri: 'https://www.wikidata.org/wiki/Q6130347',
        label: 'James Brown',
        description: 'American sportscaster'
    },
    {
        iri: 'https://dbpedia.org/page/James_Brown',
        label: 'James Brown',
        description: 'James Joseph Brown (May 3, 1933 – December 25, 2006) was an American singer, dancer, musician, record producer and bandleader. The central progenitor of funk music and a major figure of 20th century music, he is often referred to by the honorific nicknames "the Hardest Working Man in Show Business", "Godfather of Soul", "Mr. Dynamite", and "Soul Brother No. 1". In a career that lasted more than 50 years, he influenced the development of several music genres. Brown was one of the first 10 inductees into the Rock and Roll Hall of Fame at its inaugural induction in New York on January 23, 1986.'
    }],
    properties: [{
        iri: 'https://www.wikidata.org/wiki/Property:P19',
        label: 'place of birth',
        description: 'most specific known birth location of a person, animal or fictional character'
    },
    {
        iri: 'http://dbpedia.org/ontology/birthPlace',
        label: 'birthPlace',
        description: 'where the person was born'
    }],
    filters: [
        {
            subject: {
                iri: 'https://www.wikidata.org/wiki/Q5950',
                label: 'James Brown',
                description: ''
            },
            property: {
                label: 'place of birth',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            }
        },
        {
            subject: {
                iri: 'https://www.wikidata.org/wiki/Q6130347',
                label: 'James Brown',
                description: ''
            },
            property: {
                label: 'place of birth',
                iri: 'https://www.wikidata.org/wiki/Property:P19',
                description: ''
            }
        },
        {
            subject: {
                iri: 'https://dbpedia.org/page/James_Brown',
                label: 'James Brown',
                description: ''
            },
            property: {
                label: 'birthPlace',
                iri: 'https://dbpedia.org/ontology/birthPlace',
                description: ''
            }
        },
    ]
}

const queryResponseUsage: QueryResponse = {
    statements: mockStatementsUsage,
    pattern: [{
        subject: "Benzene",
        predicate: "has use",
        object: "?x"}],
    mainEntity: "Benzene",
    items: [{
        iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
        label: 'Benzene',
        description: 'Benzene is an organic chemical compound with the molecular formula C6H6. The benzene molecule is composed of six carbon atoms joined in a planar hexagonal ring with one hydrogen atom attached to each. Because it contains only carbon and hydrogen atoms, benzene is classed as a hydrocarbon. Benzene is a natural constituent of petroleum and is one of the elementary petrochemicals. Due to the cyclic continuous pi bonds between the carbon atoms and satisfying Hückel'
    },
    {
        iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID001009516',
        label: 'Benzene, Diethenyl-, Polymer With Ethenylbenzene And Ethenylethylbenzene, Chloromethylated, Trimethylamine-Quaternized, Hydroxide',
        description: 'No description available'
    },
    {
        iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3020596',
        label: 'Ethylbenzene',
        description: 'Ethylbenzene is an organic compound with the formula C6H5CH2CH3. It is a highly flammable, colorless liquid with an odor similar to that of gasoline. This monocyclic aromatic hydrocarbon is important in the petrochemical industry as a reaction intermediate in the production of styrene, the precursor to polystyrene'
    }],
    properties: [
        {
			"iri": "https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse",
			"description": "chemical functional use category",
			"label": "Chemical Functional Use"
		},
    ],
    filters: [
        {
            subject: {
                iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
                label: 'Benzene',
                description: 'Benzene is an organic chemical compound with the molecular formula C6H6...'
            },
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            }
        },
        {
            subject: {
                iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID001009516',
                label: 'Benzene, Diethenyl-, Polymer With Ethenylbenzene And Ethenylethylbenzene, Chloromethylated, Trimethylamine-Quaternized, Hydroxide',
                description: ''
            },
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            }
        },
        {
            subject: {
                iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3020596',
                label: 'Ethylbenzene',
                description: ''
            },
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            }
        },
    ]
}

const filterResponseUsage: Statement[] = [
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
            label: 'Benzene',
            description: 'Benzene is an organic chemical compound with the molecular formula C6H6...'
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Fragrance',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/61',
                description: ''
            }
        },
    },
    {
        subject: {
            iri: 'https://comptox.epa.gov/chemexpo/chemical/DTXSID3039242',
            label: 'Benzene',
            description: 'Benzene is an organic chemical compound with the molecular formula C6H6...'
        },
        snak: {
            property: {
                label: 'Chemical Functional Use',
                iri: 'https://github.ibm.com/brl-kbe/usage-kb/entity/wdt_ChemicalFunctionalUse',
                description: ''
            },
            value: {
                label: 'Propellants, non-motive (blowing agents)',
                iri: 'https://comptox.epa.gov/chemexpo/functional_use_category/90',
                description: ''
            }
        },
    },
]

const sleep = (delay: number) => {
  return new Promise((resolve) => setTimeout(resolve, delay));
};
export const handlers = [
    http.get(`${API_URL}/stores`, () => {
        return HttpResponse.json([
            { id: 'wdqs', description: 'Wikidata' },
            { id: 'dbpedia', description: 'DBpedia' },
            { id: 'pubchem', description: 'PubChem' },
            { id: 'usage-kb', description: 'UsageKB' },
        ]);
    }),

    http.post(`${API_URL}/query`, async () => {
        await sleep(5000);
        return HttpResponse.json(queryResponseUsage);
    }),
    http.post(`${API_URL}/filter`, async () => {
        await sleep(2000);
        return HttpResponse.json(filterResponseUsage);
    }),
];
