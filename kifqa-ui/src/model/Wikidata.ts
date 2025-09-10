// src/model/Wikidata.ts
import React from 'react';
import { Type } from 'class-transformer';
import { IsString, ValidateNested } from 'class-validator';

export class Entity {
    @IsString()
    iri!: string;
    @IsString()
    label!: string;
    @IsString()
    description!: string;
}
export class Item extends Entity { }

export class Property extends Entity { }

export class Datavalue {
    type?: string;
    value!: string;
}

export class Snak {
    @ValidateNested()
    @Type(() => Property)
    property!: Property;

    @ValidateNested()
    @Type(() => Item)
    value!: Item
}

export class Rank {
    snaks?: Record<string, Snak[]>;
}

export class Statement {
    @ValidateNested()
    @Type(() => Item)
    subject!: Item;

    @ValidateNested()
    @Type(() => Snak)
    snak!: Snak;
    // rank?: Rank;
    @ValidateNested({ each: true })
    @Type(() => Snak)
    qualifiers?: Snak[];

    @ValidateNested({ each: true })
    @Type(() => Snak)
    references?: Snak[];
}

export class LinkedEntity {
    iri!: string
    label!: string
    description!: string
}

export class Triple {
    subject!: string
    predicate!: string
    object!: string
}

export class Filter {
    subject?: Entity
    property?: Property
    value?: Entity
}



export class QueryResponse {
    @ValidateNested({ each: true })
    @Type(() => Statement)
    statements?: Statement[]
    @ValidateNested({ each: true })
    @Type(() => Triple)
    pattern?: Triple[]
    @ValidateNested({ each: true })
    @Type(() => Filter)
    filters?: Filter[]
    @IsString()
    mainEntity?: string
    @ValidateNested({ each: true })
    @Type(() => LinkedEntity)
    items?: LinkedEntity[]
    @ValidateNested({ each: true })
    @Type(() => LinkedEntity)
    properties?: LinkedEntity[]
}
