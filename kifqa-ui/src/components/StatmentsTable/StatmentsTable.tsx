import React from 'react';
import { Statement } from 'model/Wikidata';
import {
    Box,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableRow,
    Tooltip,
    Paper,
    Typography,
    Link,
} from '@mui/material';
import { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';


interface Props {
    statements: Statement[];
}

const entityFontSize = 14
const propertyFontSize = 16
const qualifierFontSize = 12

export const StatementsTable: React.FC<Props> = ({ statements }) => {
    const grouped = statements.reduce<Record<string, Statement[]>>((acc, stmt) => {
        const subjectIRI = stmt.subject.iri;
        if (!acc[subjectIRI]) acc[subjectIRI] = [];
        acc[subjectIRI].push(stmt);
        return acc;
    }, {});

    const entries = Object.entries(grouped);

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

    return (
        <>
            <Box sx={{
                width: '100%',
                maxWidth: { xs: '100%', sm: '90%', md: '80%' },
                marginLeft: 'auto',
                marginRight: 'auto',
            }}>
                <h3>Statements</h3>
            </Box>
            {entries.map(([subjectIRI, stmts], groupIndex) => (
                <TableContainer key={`${subjectIRI}-${groupIndex}`} component={Paper} sx={{
                    width: '100%',
                    maxWidth: { xs: '100%', sm: '90%', md: '80%' },
                    marginLeft: 'auto',
                    marginRight: 'auto',
                    mb: 1.2
                }}>
                    <Table>
                        <TableBody>
                            {stmts.map((stmt, index) => (
                                <TableRow key={`${subjectIRI}-${index}`}>
                                    {index === 0 && (
                                        <TableCell
                                            align="left"
                                            sx={{
                                                backgroundColor: '#eaecf0',
                                                borderBottom: 'none',
                                                verticalAlign: 'top',
                                                paddingTop: 1,
                                                paddingLeft: 1,
                                                width: '20%',
                                                maxWidth: '25%'
                                            }}>
                                            <HtmlTooltip 
                                                title={
                                                    <React.Fragment>
                                                        <Typography color="inherit">{stmt.subject.label}</Typography>
                                                        {stmt.subject.description}
                                                    </React.Fragment>
                                                    }
                                                placement="right-start"
                                            >
                                                <Link sx={{ textDecoration: 'none', fontSize: entityFontSize }} href={subjectIRI} target="_blank" rel="noopener noreferrer">
                                                    <strong >{stmt.subject.label}</strong>
                                                </Link>
                                            </HtmlTooltip>
                                        </TableCell>
                                    )}
                                    {index != 0 && (
                                        <TableCell align="left"
                                            sx={{
                                                backgroundColor: '#eaecf0',
                                                verticalAlign: 'top',
                                                paddingTop: 1,
                                                paddingLeft: 1,
                                                width: '20%',
                                                maxWidth: '25%'
                                            }}>
                                        </TableCell>
                                    )}
                                    <TableCell align="left" sx={{
                                        verticalAlign: 'top',
                                        paddingTop: 1,
                                        paddingLeft: 1,
                                        width: '20%',
                                        maxWidth: '25%'
                                    }}>
                                        <Box sx={{ mb: 1 }}>
                                            <Typography>
                                                <HtmlTooltip 
                                                    title={
                                                        <React.Fragment>
                                                            <Typography color="inherit">{stmt.snak.property.label}</Typography>
                                                            {stmt.snak.property.description}
                                                        </React.Fragment>
                                                        }
                                                    placement="right-start"
                                                >
                                                    <Link sx={{ textDecoration: 'none', fontSize: propertyFontSize }} href={stmt.snak.property.iri} target="_blank" rel="noopener noreferrer">
                                                        {stmt.snak.property.label}
                                                    </Link>
                                                </HtmlTooltip>


                                            </Typography>
                                            {/* References */}
                                            {/* {stmt.references && stmt.references.length > 0 && (
                                                    <Button
                                                        sx={{
                                                            ml: 1,
                                                            px: 0.5,
                                                            py: 0,
                                                            bgcolor: 'primary.main',
                                                            color: 'primary.contrastText',
                                                            borderRadius: '4px',
                                                            fontSize: 11,
                                                            fontWeight: 'bold',
                                                            cursor: 'default',
                                                            userSelect: 'none',
                                                        }}
                                                        >
                                                        {stmt.references.length} references
                                                    </Button>
                                            )} */}
                                        </Box>
                                    </TableCell>
                                    <TableCell align="left" sx={{ verticalAlign: 'top', paddingTop: 1, paddingLeft: 1 }}>
                                        <Box sx={{ mb: 1 }}>
                                            <Typography>
                                                <HtmlTooltip 
                                                    title={
                                                        <React.Fragment>
                                                            <Typography color="inherit">{stmt.snak.value.label}</Typography>
                                                            {stmt.snak.value.description}
                                                        </React.Fragment>
                                                        }
                                                    placement="right-start"
                                                >
                                                    <Link sx={{ textDecoration: 'none', fontSize: propertyFontSize }} href={stmt.snak.value.iri} target="_blank" rel="noopener noreferrer">
                                                        {stmt.snak.value.label}
                                                    </Link>
                                                </HtmlTooltip>
                                            </Typography>
                                            {/* Qualifiers */}
                                            {stmt.qualifiers && stmt.qualifiers.map((qualifier, index) => (
                                                <Typography
                                                    key={index}
                                                    sx={{ pl: 2, fontSize: 11, color: 'text.secondary' }}
                                                >
                                                    <span style={{ whiteSpace: 'nowrap' }}>
                                                        <Link
                                                            style={{ textDecoration: 'none', fontSize: qualifierFontSize, marginRight: 70 }}
                                                            href={qualifier.property.iri}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                        >
                                                            {qualifier.property.label}
                                                        </Link>
                                                        <Link
                                                            style={{ textDecoration: 'none', fontSize: qualifierFontSize }}
                                                            href={qualifier.value.iri}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                        >
                                                            {qualifier.value.label}
                                                        </Link>
                                                    </span>
                                                </Typography>
                                            ))}
                                        </Box>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>

                </TableContainer>
            ))}
        </>
    );
};
