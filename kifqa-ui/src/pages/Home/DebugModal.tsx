import React, { useState }from 'react';
import {
    Button, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions,
    Divider, Grid, IconButton, Link, TextField, Tooltip, Typography,
} from '@mui/material';
import { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';

import { RemoveCircleOutline } from '@mui/icons-material';
import { FilterValues } from '@pages/Home/Home'


import {
    Filter, LinkedEntity, Triple,

} from '../../model/Wikidata';

interface Props {
    debugOpen: boolean;
    stores: string[];
    query: string;
    annotated: boolean;
    triples: Triple[];
    filters?: Filter[];
    linkedEntities?: LinkedEntity[];
    linkedProperties?: LinkedEntity[];
    onClose: () => void;
    onRun: (data: FilterValues) => void
    onUpdateFilters?: (filters: Filter[]) => void;
    onUpdateEntities?: (entities: LinkedEntity[]) => void;
    onUpdateProperties?: (properties: LinkedEntity[]) => void;
}


export const DebugModal: React.FC<Props> = ({
    debugOpen,
    stores = [],
    annotated,
    filters = [],
    triples,
    linkedEntities = [],
    linkedProperties = [],
    onClose,
    onRun,
    onUpdateFilters,
    onUpdateEntities,
    onUpdateProperties,
}) => {
    const [loading, setLoading] = useState(false);

    const HtmlTooltip = styled(({ className, ...props }: TooltipProps) => (
        <Tooltip {...props} classes={{ popper: className }} />
    ))(({ theme }) => ({
        [`& .${tooltipClasses.tooltip}`]: {
            backgroundColor: '#f5f5f9',
            color: 'rgba(0, 0, 0, 0.87)',
            maxWidth: 220,
            fontSize: theme.typography.pxToRem(12),
            border: '1px solid #dadde9',
        },
    }));

    const handleDeleteLinkedItem = (index: number) => {
        const entityToRemove = linkedEntities?.[index];
        if (!entityToRemove) return;

        const updatedEntities = linkedEntities.filter((_, i) => i !== index);
        onUpdateEntities?.(updatedEntities);

        const updatedFilters = filters.filter(
            f => f.subject?.iri !== entityToRemove.iri && f.value?.iri !== entityToRemove.iri
        );
        onUpdateFilters?.(updatedFilters);
    };

    const handleDeleteLinkedProperty = (index: number) => {
        const propertyToRemove = linkedProperties?.[index];
        if (!propertyToRemove) return;

        const updatedProperties = linkedProperties.filter((_, i) => i !== index);
        onUpdateProperties?.(updatedProperties);

        const updatedFilters = filters.filter(
            f => f.property?.iri !== propertyToRemove.iri
        );
        onUpdateFilters?.(updatedFilters);
    };

    return (
        <Dialog open={debugOpen} onClose={onClose} maxWidth="md" fullWidth>

            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                Details
                <Button onClick={onClose}color="primary" size="small">
                    Close
                </Button>
            </DialogTitle>
            <DialogContent>
                {/* Triples Section */}
                <Typography variant="h6">
                    Draft Triple Pattern
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {triples?.map((triple, index) => (
                    <Grid container spacing={2} marginTop={1} alignItems="center" key={index}>
                        <Grid style={{ flex: 4 }}>
                            <TextField
                                label="Subject"
                                value={triple.subject}
                                fullWidth
                            />
                        </Grid>
                        <Grid style={{ flex: 4 }}>
                            <TextField
                                label="Predicate"
                                value={triple.predicate}
                                fullWidth
                            />
                        </Grid>
                        <Grid style={{ flex: 4 }}>
                            <TextField
                                label="Object"
                                value={triple.object}
                                fullWidth
                            />
                        </Grid>
                    </Grid>
                ))}

                {/* Linked Items Section */}
                <Typography variant="h6" mt={3}>
                    Linked Items
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {/* Column headers */}
                <Grid container spacing={1} sx={{ fontWeight: "bold", mb: 1 }}>
                    <Grid style={{ flex: 3 }}>Item</Grid>
                    <Grid style={{ flex: 7 }}>Description</Grid>
                    <Grid style={{ flex: "0 0 auto" }}></Grid>
                </Grid>

                {linkedEntities && linkedEntities.map((linkedEntity, index) => (
                    <Grid
                        container
                        spacing={1}
                        alignItems="center"
                        key={index}
                        sx={{ borderBottom: "1px solid #ddd", py: 0.5 }}
                    >
                        <Grid style={{ flex: 3.25 }}>
                            <Link href={linkedEntity.iri} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none', fontSize: 18 }}>
                                <HtmlTooltip
                                    title={
                                        <React.Fragment>
                                            <Typography color="inherit">{linkedEntity.label}</Typography>
                                            {linkedEntity.description}
                                        </React.Fragment>
                                        }
                                >
                                    <Typography variant="body2">
                                        <strong >{linkedEntity.label}</strong>
                                    </Typography>
                                </HtmlTooltip>
                            </Link>
                        </Grid>
                        <Grid style={{ flex: 7 }}>
                            <Typography variant="body2">{linkedEntity.description}</Typography>
                        </Grid>
                        <Grid style={{ flex: "0 0 auto" }}>
                            <IconButton
                                color="error"
                                onClick={() => handleDeleteLinkedItem(index)}
                            >
                                <RemoveCircleOutline />
                            </IconButton>
                        </Grid>
                    </Grid>
                ))}

                {/* Linked Properties Section */}
                <Typography variant="h6" mt={3}>
                    Linked Properties
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {/* Column headers */}
                <Grid container spacing={1} sx={{ fontWeight: "bold", mb: 1 }}>
                    <Grid style={{ flex: 3 }}>Property</Grid>
                    <Grid style={{ flex: 7 }}>Description</Grid>
                    <Grid style={{ flex: "0 0 auto" }}></Grid>
                </Grid>

                {linkedProperties && linkedProperties.map((linkedProperty, index) => (
                    <Grid
                        container
                        spacing={1}
                        alignItems="center"
                        key={index}
                        sx={{ borderBottom: "1px solid #ddd", py: 0.5 }}
                    >
                        <Grid style={{ flex: 3.25 }}>
                            <Link href={linkedProperty.iri} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none', fontSize: 18 }}>
                                <HtmlTooltip
                                    title={
                                        <React.Fragment>
                                            <Typography color="inherit">{linkedProperty.label}</Typography>
                                            {linkedProperty.description}
                                        </React.Fragment>
                                        }
                                >
                                    <Typography variant="body2">

                                        <strong >{linkedProperty.label}</strong>
                                    </Typography>
                                </HtmlTooltip>
                            </Link>
                        </Grid>
                        <Grid style={{ flex: 7 }}>
                            <Typography variant="body2">{linkedProperty.description}</Typography>
                        </Grid>
                        <Grid style={{ flex: "0 0 auto" }}>
                            <IconButton
                                color="error"
                                onClick={() => handleDeleteLinkedProperty(index)}
                            >
                                <RemoveCircleOutline />
                            </IconButton>
                        </Grid>
                    </Grid>
                ))}

                {/* Linked Properties Section */}
                <Typography variant="h6" mt={3}>
                    Filters
                </Typography>
                <Divider sx={{ mb: 2 }} />

                {/* Column headers */}
                <Grid container spacing={1} sx={{ fontWeight: "bold", mb: 1 }}>
                    <Grid style={{ flex: 4 }}>Subject</Grid>
                    <Grid style={{ flex: 4 }}>Property</Grid>
                    <Grid style={{ flex: 4 }}>Value</Grid>
                    <Grid style={{ flex: "0 0 auto" }}></Grid>
                </Grid>

                {filters && filters.map((filter, index) => (
                    <Grid
                        container
                        spacing={1}
                        alignItems="center"
                        key={index}
                        sx={{ borderBottom: "1px solid rgba(221, 221, 221, 1)", py: 0.5 }}
                    >
                        <Grid style={{ flex: 4 }}>
                            {filter.subject && <Link href={filter.subject.iri} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none', fontSize: 18 }}>
                                <HtmlTooltip
                                    title={
                                        <React.Fragment>
                                            <Typography color="inherit">{filter.subject.label}</Typography>
                                            {filter.subject.description}
                                        </React.Fragment>
                                        }
                                >
                                    <Typography variant="body2">
                                        <strong >{filter.subject.label}</strong>
                                    </Typography>
                                </HtmlTooltip>
                            </Link>}
                            {!filter.subject && <Typography variant="body2"></Typography>}
                        </Grid>
                        <Grid style={{ flex: 4 }}>
                            {filter.property && <Link href={filter.property.iri} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none', fontSize: 18 }}>
                                <HtmlTooltip
                                    title={
                                        <React.Fragment>
                                            <Typography color="inherit">{filter.property.label}</Typography>
                                            {filter.property.description}
                                        </React.Fragment>
                                        }
                                >
                                    <Typography variant="body2">
                                        <strong >{filter.property.label}</strong>
                                    </Typography>
                                </HtmlTooltip>
                            </Link>}
                            {!filter.property && <Typography variant="body2"></Typography>}
                        </Grid>
                        <Grid style={{ flex: 4 }}>
                            {filter.value && <Link href={filter.value.iri} target="_blank" rel="noopener noreferrer" sx={{ textDecoration: 'none', fontSize: 18 }}>
                                <Typography variant="body2">
                                    <strong >{filter.value.label}</strong>
                                </Typography>
                            </Link>}
                            {!filter.value && <Typography variant="body2"></Typography>}
                        </Grid>
                    </Grid>
                ))}
            </DialogContent>
            <DialogActions>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => onRun({
                        filters: filters,
                        stores: stores,
                        annotated: annotated,
                    })}
                    disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Run'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};
