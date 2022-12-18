grammar HassILGrammar;

document
   : (sentence)+
   ;

sentence
   : expression EOL
   ;

expression
   : (group | optional | text_chunk | list | rule) (alt? expression)*
   ;

// One or more text chunks in a sequence
group
   : '(' expression ')'
   ;

optional
   : '[' expression ']'
   ;

alt
   : '|'
   ;

text_chunk
   : STRING
   ;

list
   : '{' list_name '}'
   ;

list_name
   : STRING
   ;

rule
   : '<' rule_name '>'
   ;

rule_name
   : STRING
   ;

STRING
   : (ESC | CHARACTER)+
   ;

ESC
   : '\\' [<>()[\]{}|]
   ;

CHARACTER
   : ~ [<>()[\]{}\n\r|]
   ;

EOL
   : [\n\r] +
   ;
